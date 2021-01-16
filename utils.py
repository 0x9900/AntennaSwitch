#
#
import gc
import logging
import network
import time
import uasyncio as asyncio

from machine import Pin
from machine import WDT

HEARTBEAT_LED = 2

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('utils.py')

class APorts:
  def __init__(self, ports):
    self.ports = ports

  def all_off(self):
    for gpio, _ in self.ports.values():
      gpio.off()

  def on(self, port):
    self.ports[port][0].on()

  def off(self, port):
    self.ports[port][0].off()

  def label(self, port):
    return self.ports[port][1]

  def items(self):
    return self.ports.items()

  def keys(self):
    return self.ports.keys()

  def __contains__(self, key):
    return key in self.ports


def wifi_connect(ssid, password):
  ap_if = network.WLAN(network.AP_IF)
  ap_if.active(False)
  sta_if = network.WLAN(network.STA_IF)
  if not sta_if.isconnected():
    LOG.info('Connecting to WiFi...')
    sta_if.active(True)
    sta_if.connect(ssid, password)
    while not sta_if.isconnected():
      time.sleep(1)
  LOG.info('Network config: %s', sta_if.ifconfig())
  gc.collect()
  return sta_if

async def heartbeat():
  await asyncio.sleep(20)
  speed = 125
  led = Pin(HEARTBEAT_LED, Pin.OUT, value=1)
  wdt = WDT()
  while True:
    led(0)
    wdt.feed()
    await asyncio.sleep_ms(speed)
    led(1)
    wdt.feed()
    await asyncio.sleep_ms(speed * 10)

def parse_headers(head_lines):
  headers = {}
  for line in head_lines:
    if line.startswith(b'GET') or line.startswith(b'POST'):
      method, uri, proto = line.split()
      headers[b'Method'] = method
      headers[b'URI'] = uri
      headers[b'Protocol'] = proto
    else:
      try:
        key, val = line.split(b":", 1)
        headers[key] = val
      except:
        LOG.warning('header line warning: %s', line)
  return headers
