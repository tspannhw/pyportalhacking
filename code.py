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

import adafruit_esp32spi.adafruit_esp32spi_socket as socket

# Requests 
import adafruit_requests as requests
 
# Import NeoPixel Library
import neopixel
 
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

# Initialize a requests object with a socket and esp32spi interface
requests.set_socket(socket, wifi)

JSON_POST_URL = "http://tspann-mbp15-hw14277:9989/pyportal"

# Set up ADT7410 sensor
i2c_bus = busio.I2C(board.SCL, board.SDA)
adt = adafruit_adt7410.ADT7410(i2c_bus, address=0x48)
adt.high_resolution = True
 
# Set up an analog light sensor on the PyPortal
adc = AnalogIn(board.LIGHT)
 
while True:
    try:
        light_value = adc.value
        print('Light Level: ', light_value)
        temperature = adt.temperature
        print('Temperature: %0.2f C'%(temperature))
        data = {"light":light_value, "temperature": temperature} 
        response = requests.post(JSON_POST_URL, data=data)
        json_resp = response.json()
        # Parse out the 'data' key from json_resp dict.
        print("Data received from server:", json_resp['data'])
        print('-'*40)
        response.close()

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        continue
    print('Delaying {0} seconds...'.format(IO_DELAY))
    time.sleep(IO_DELAY)
