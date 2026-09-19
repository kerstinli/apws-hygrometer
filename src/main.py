#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
import requests
from adafruit_ads1x15.analog_in import AnalogIn

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# 5 minutes
ticktack = 5 * 60

# Voltage divider:
# R1 = resistor from AOUT to ADC
# R2 = resistor from ADC to GND
R1 = 10_000.0
R2 = 20_000.0

# Calibration
# Adjust these values to your sensor later.
#
# SENSOR_DRY = voltage at dry substrate
# SENSOR_WET = voltage at very wet substrate
#
# For this sensor type, "dry" typically has
# a higher voltage than "wet".
SENSOR_DRY = 3.0
SENSOR_WET = 1.2

# ------------------------------------------------------------
# Initialize I2C
# ------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# ADS1115 input A0
channel = AnalogIn(ads, 0)

# Measurement range ±4.096 V
# Since our voltage divider delivers max approx. 3.33 V,
# this range is well suited.
ads.gain = 1


def moisture_percent(voltage):
    """
    Calculates a simple moisture value
    from 0 to 100 %.
    0 % = dry
    100 % = wet
    """

    # Conversion:
    #
    # SENSOR_DRY -> 0 %
    # SENSOR_WET -> 100 %
    percent = (
            (SENSOR_DRY - voltage)
            / (SENSOR_DRY - SENSOR_WET)
            * 100
    )

    # Limit to 0...100 %
    percent = max(0, min(100, percent))
    return percent


def execute(logstash_url: str) -> None:
    logging.info("AZ-Delivery Hygrometer V1.2")
    try:
        while True:
            try:
                adc_value = channel.value
                adc_voltage = channel.voltage
                voltage = adc_voltage * (R1 + R2) / R2

                logging.info(f"ADC: {adc_value:5.1f} %")
                logging.info(f"ADC voltage: {adc_voltage:5.1f} %")
                logging.info(f"Voltage: {voltage:5.1f} %")

                moisture = moisture_percent(voltage)

                hygrometer_data = {
                    "moisture": round(moisture, 1),
                }
                response = requests.post(
                    logstash_url,
                    json=hygrometer_data,
                    timeout=10,
                )
                response.raise_for_status()
            except RuntimeError as error:
                logging.error(f"Error getting values from sensor: {error}")
            except requests.exceptions.RequestException as error:
                logging.error(f"Error sending data to Logstash: {error}")

            time.sleep(ticktack)

    except KeyboardInterrupt:
        logging.info("Cancel execution...")

    finally:
        i2c.deinit()

if __name__ == "__main__":
    # The API endpoint - can be overridden by environment variable or command-line argument
    logstash_url: str = os.getenv("LOGSTASH_URL", "http://logstash:5044")

    parser = argparse.ArgumentParser(description="DHT11 Sensor to Logstash")
    parser.add_argument(
        "--logstash-url",
        help="Logstash endpoint URL (overrides LOGSTASH_URL environment variable)",
    )
    args = parser.parse_args()
    if args.logstash_url:
        logstash_url = args.logstash_url

    execute(logstash_url)
