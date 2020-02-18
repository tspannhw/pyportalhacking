"""
PyPortal IOT Data Logger for Adafruit IO
 
Dependencies:
    * CircuitPython_ADT7410
        https://github.com/adafruit/Adafruit_CircuitPython_ADT7410
 
    * CircuitPython_AdafruitIO
        https://github.com/adafruit/Adafruit_CircuitPython_AdafruitIO
"""
import time
import board
import busio
from digitalio import DigitalInOut
from analogio import AnalogIn
 
# ESP32 SPI
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager

# Import NeoPixel Library
import neopixel
 
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
 
# Import ADT7410 Library
import adafruit_adt7410
 
# Timeout between sending data to Apache NiFi, in seconds
IO_DELAY = 30
 
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
 
# PyPortal ESP32 Setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)
 
# Connect to WiFi
wifi.connect()
 
# Set up ADT7410 sensor
i2c_bus = busio.I2C(board.SCL, board.SDA)
adt = adafruit_adt7410.ADT7410(i2c_bus, address=0x48)
adt.high_resolution = True

# Set up an analog light sensor on the PyPortal
adc = AnalogIn(board.LIGHT)
 
if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])
 
for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap['ssid'], 'utf-8'), ap['rssi']))

print("Connected to", str(esp.ssid, 'utf-8'), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))
print("IP lookup nifi serer: %s" % esp.pretty_ip(esp.get_host_by_name("tspann-mbp15-hw14277")))
print("Ping nifi server: %d ms" % esp.ping("tspann-mbp15-hw14277"))

while True:
    try:
        light_value = adc.value
        print('Light Level: ', light_value)
        #temperature = adt.temperature
        #print('Temperature: %s C' %  temperature)
        data = {"light":light_value}
        #, "temperature": temperature} 
        print('Data: %s' % data)
        response = wifi.post("http://192.168.1.249:9989/pyportal", json=data)
        json_resp = response.json()
        response.close()
        print('After wifi')

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        continue
    print('Delaying {0} seconds...'.format(IO_DELAY))
    response = None
    time.sleep(IO_DELAY)
