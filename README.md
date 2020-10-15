# Remote Antenna Switch

## This work is in progress

This Remote Coax Switch lets you remotely using your home WiFi, switch
up to four HF antennas. The DC power used by the switch is injected
into the coax power using a Bias T. There is no need to run long wires
from your radioshack to the antenna. This switch is also controllable
using the internet. Making it ideal for operating a remote station.

## Switch controller

The controller board host an [ESP8266 Wemos D1][1]
micro-controller. It takes up to 14 volts in input and up to 4
switches can be connected. The antenna controller is programmed in
[MicroPython][2].

The main goal for this controller is to develop an HF antenna switch
but you can use this controller for any other DIY project.

The schematics and PCB can be found on [EasyEDA][3]

![First prototype](misc/IMG_0680.JPG)

## Controlling the switch

### Using the web Interface

![First prototype](misc/ASWeb.png)

### Using the terminal

The antenna can be selected from the terminal with the following command.
Replace the `1` after the word select with the switch number.

    √ ~ % curl -s http://192.168.10.148:8088/api/v1/select/1 | ppjson
    {
        "port": 1,
        "msg": "Port 1 selected",
        "status": "OK"
    }

You can request the status of all the ports using the following command.

    curl -s http://192.168.10.148:8088/api/v1/ports | ppjson
    {
        "4": {
            "label": "N/C",
            "status": 0
        },
        "1": {
            "label": "Hustler",
            "status": 1
        },
        "2": {
            "label": "Dipole 40/80",
            "status": 0
        },
        "3": {
            "label": "Isotropic",
            "status": 0
        }
    }



[1]: https://docs.wemos.cc/en/latest/d1/d1_mini.html
[2]: https://micropython.org
[3]: https://easyeda.com/W6BSD/antennaswitch
