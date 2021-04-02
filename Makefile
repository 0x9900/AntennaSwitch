#
# Make sure to define the right PORT
# Check the FLASH_SIZE. My Wemos D1 had 4MB
#

PORT = /dev/cu.SLAB_USBtoUART3
#PORT = /dev/cu.wchusbserial1110

SPEED = 115200
FLASH_SIZE = 4MB

# Path to programs
ESPTOOL = /opt/local/bin/esptool --port $(PORT) --baud $(SPEED)
AMPY = /opt/local/bin/ampy --delay 1 --port $(PORT) --baud $(SPEED)
CROSS = /Users/fred/src/micropython/mpy-cross/mpy-cross

FIRMWARE = ~/Downloads/esp8266-20210202-v1.14.bin

SOURCES = lib/logging.mpy config.mpy proto.mpy utils.mpy
HTML = html/index.html html/style.css

.SUFFIXES: .py .mpy
.PHONY: upload erase flash

.py.mpy:
	$(CROSS) $<

cross: ${SOURCES}

upload: ${SOURCES}
	@echo "Uploading files"
	@for file in $(SOURCES); do \
	echo "$$file"; \
	$(AMPY) put $$file $$file; \
	done
	@echo "main.py"
	@$(AMPY) put main.py

upload_html: $(HTML)
	@echo "Uploading html files"
	@for file in $(HTML); do \
	$(AMPY) put $$file $$file; \
	echo "$$file"; \
	done
	@echo Done

erase:
	$(ESPTOOL) erase_flash

flash_pro: erase
	@echo "Flash Wemos D1 Pro: please check the MEMORY SIZE"
	$(ESPTOOL) write_flash --flash_size=$(FLASH_SIZE) 0 $(FIRMWARE)
	@echo 'Power device again'

flash: erase
	@echo "Flash Wemos D1 mini"
	$(ESPTOOL) write_flash --flash_size=detect -fm dio 0 $(FIRMWARE)
	@echo 'Power device again'

info:
	$(ESPTOOL) chip_id
