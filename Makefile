#
# Make sure to define the right PORT
# Check the FLASH_SIZE. My Wemos D1 had 4MB
#

PORT = /dev/cu.SLAB_USBtoUART3
SPEED = 115200
FLASH_SIZE = 4MB

# Path to programs
ESPTOOL = /opt/local/bin/esptool --port $(PORT) --baud $(SPEED)
AMPY = /opt/local/bin/ampy --port $(PORT) --baud $(SPEED)
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
	@echo "main.py"
	@$(AMPY) put main.py
	@for file in $(SOURCES); do \
	echo "$$file"; \
	$(AMPY) put $$file $$file; \
	done

upload_html: $(HTML)
	@echo "Uploading html files"
	@for file in $(HTML); do \
	$(AMPY) put $$file $$file; \
	echo "$$file"; \
	done
	@echo Done

erase:
	$(ESPTOOL) --port $(PORT) erase_flash

flash:
	@echo "Be sure about MEMORY SIZE"
	$(ESPTOOL) --port $(PORT) --baud 115200 write_flash --verify --flash_size=$(FLASH_SIZE) 0 $(FIRMWARE)
	@echo 'Power device again'
