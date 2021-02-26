#
#
import gc
import logging
import time
import uasyncio as asyncio
import ujson
import uselect as select
import usocket as socket

import config
from utils import *


__version__ = "1.1"

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger('ANTENNA')

HTML_PATH = b'/html'

HTML_ERROR = """<!DOCTYPE html><html><head><title>404 Not Found</title>
<body><h1>{} {}</h1></body></html>
"""

HTTPCodes = {
  200: ('OK', 'OK'),
  303: ('Moved', 'Moved'),
  307: ('Temporary Redirect', 'Moved temporarily'),
  400: ('Bad Request', 'Bad request'),
  404: ('Not Found', 'File not found'),
  500: ('Internal Server Error', 'Server erro'),
}

MIME_TYPES = {
  b'css': 'text/css',
  b'html': 'text/html',
  b'js': 'application/javascript',
  b'json': 'application/json',
  b'txt': 'text/plain',
}


class Server:

  def __init__(self, ports, addr='0.0.0.0', port=8088):
    self.addr = addr
    self.port = port
    self.open_socks = []
    self.ports = ports

  async def run(self, loop):
    addr = socket.getaddrinfo(self.addr, self.port, 0, socket.SOCK_STREAM)[0][-1]
    s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s_sock.bind(addr)
    s_sock.listen(5)
    self.open_socks.append(s_sock)
    LOG.info('Awaiting connection on %s:%d', self.addr, self.port)

    poller = select.poll()
    poller.register(s_sock, select.POLLIN)
    while True:
      if poller.poll(1):  # 1ms
        c_sock, addr = s_sock.accept()  # get client socket
        LOG.info('Connection from %s:%d', *addr)
        loop.create_task(self.process_request(c_sock))
      await asyncio.sleep_ms(100)

  async def process_request(self, sock):
    LOG.info('Process request %s', sock)
    self.open_socks.append(sock)
    sreader = asyncio.StreamReader(sock)
    swriter = asyncio.StreamWriter(sock, '')
    try:
      head_lines = []
      while True:
        line = await sreader.readline()
        line = line.rstrip()
        if line in (b'', b'\r\n'):
          break
        head_lines.append(line)

      headers = parse_headers(head_lines)
      uri = headers.get(b'URI')
      if not uri:
        LOG.debug('Empty request')
        raise OSError

      LOG.info('Request %s %s', headers[b'Method'].decode(), uri.decode())
      if uri == b'/' or uri == b'/index.html':
        await self.send_file(swriter, b'/index.html')
      elif uri == b'/api/v1/ports':
        await self.get_ports(swriter)
      elif uri.startswith('/api/v1/select/'):
        await self.switch_antenna(swriter, uri)
      else:
        await self.send_file(swriter, uri)
    except OSError:
      pass

    gc.collect()
    LOG.debug('Disconnecting %s / %d', sock, len(self.open_socks))
    sock.close()
    self.open_socks.remove(sock)

  async def switch_antenna(self, wfd, uri):
    try:
      port = uri.split(b'/')[-1]
      if not port.isdigit():
        raise ValueError

      port = int(port)
      if port not in self.ports:
        raise KeyError

      self.ports.all_off()
      await asyncio.sleep_ms(10)
      self.ports.on(port)
    except (KeyError, ValueError):
      await self.send_json(wfd, {'status': 'ERROR',
                                 'msg': 'Invalid port {}'.format(port)})
    else:
      await self.send_json(wfd, {'status': 'OK', 'port': port,
                                 'msg': 'Port {:d} selected'.format(port)})

  async def get_ports(self, wfd):
    data = {}
    for port, pdata in sorted(self.ports.items()):
      gpio, label = pdata
      data[port] = {'status': gpio.value(), 'label': label}
    await self.send_json(wfd, data)
    gc.collect()

  async def send_json(self, wfd, data):
    LOG.debug('send_json')
    jdata = ujson.dumps(data)
    await wfd.awrite(self._headers(200, b'json', content_len=len(jdata)))
    await wfd.awrite(jdata)
    gc.collect()

  async def send_file(self, wfd, url):
    LOG.debug('send_file: %s', url)
    fpath = b'/'.join([HTML_PATH, url.lstrip(b'/')])
    mime_type = fpath.split(b'.')[-1]

    try:
      with open(fpath, 'rb') as fd:
        await wfd.awrite(self._headers(200, mime_type, cache=-1))
        await wfd.awrite(fd.read())
    except OSError as err:
      LOG.debug('send file error: %s %s', err, url)
      await self.send_error(wfd, 404)
    gc.collect()

  async def send_error(self, wfd, err_c):
    if err_c not in HTTPCodes:
      err_c = 400
    errors = HTTPCodes[err_c]
    await wfd.awrite(self._headers(err_c) + HTML_ERROR.format(err_c, errors[1]))
    gc.collect()

  async def send_redirect(self, wfd, location='/'):
    page = HTML_ERROR.format(303, 'redirect')
    await wfd.awrite(self._headers(303, location=location, content_len=len(page)))
    await wfd.awrite(HTML_ERROR.format(303, 'redirect'))
    gc.collect()

  def close(self):
    LOG.debug('Closing %d sockets', len(self.open_socks))
    for sock in self.open_socks:
      sock.close()

  @staticmethod
  def _headers(code, mime_type=None, location=None, content_len=0, cache=None):
    try:
      labels = HTTPCodes[code]
    except KeyError:
      raise KeyError('HTTP code (%d) not found', code)
    headers = []
    headers.append(b'HTTP/1.1 {:d} {}'.format(code, labels[0]))
    headers.append(b'Content-Type: {}'.format(MIME_TYPES.get(mime_type, 'text/html')))
    if location:
      headers.append(b'Location: {}'.format(location))
    if content_len:
      headers.append(b'Content-Length: {:d}'.format(content_len))

    if cache and cache == -1:
      headers.append(b'Cache-Control: public, max-age=604800, immutable')
    elif cache and isinstance(cache, str):
      headers.append(b'Cache-Control: '.format(cache))
    headers.append(b'Connection: close')

    return b'\n'.join(headers) + b'\n\n'

def main():
  print("\n\nAntenna Switch version: {}\n".format(__version__))
  ports = APorts(config.PORTS)
  LOG.info('Default port: %s on', config.DEFAULT_PORT)
  ports.on(config.DEFAULT_PORT)
  wifi_connect(config.SSID, config.PASSWORD)
  server = Server(ports=ports)

  loop = asyncio.get_event_loop()
  loop.create_task(server.run(loop))
  loop.create_task(heartbeat())
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    LOG.info('Program interrupted')
  finally:
    server.close()

if __name__ == "__main__":
    main()
