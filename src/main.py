#!/usr/bin/env python3

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
import requests
import time
from adafruit_ads1x15.analog_in import AnalogIn

# The API endpoint
logstash_url = "http://logstash:5044"

# ------------------------------------------------------------
# Einstellungen
# ------------------------------------------------------------

# 5 Minuten in Sekunden
SENDEINTERVALL = 5 * 60

# Spannungsteiler:
# R1 = Widerstand von AOUT zum ADC
# R2 = Widerstand vom ADC nach GND
R1 = 10_000.0
R2 = 20_000.0

# Kalibrierung
# Diese Werte später an deinen Sensor anpassen.
#
# SENSOR_TROCKEN = Spannung bei trockenem Substrat
# SENSOR_NASS = Spannung bei sehr nassem Substrat
#
# Bei diesem Sensortyp ist "trocken" typischerweise
# eine höhere Spannung als "nass".
SENSOR_TROCKEN = 3.0
SENSOR_NASS = 1.2

# ------------------------------------------------------------
# I2C initialisieren
# ------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# ADS1115 Eingang A0
channel = AnalogIn(ads, 0)

# Messbereich ±4.096 V
# Da unser Spannungsteiler maximal ca. 3.33 V liefert,
# ist dieser Bereich gut geeignet.
ads.gain = 1


# ------------------------------------------------------------
# Funktionen
# ------------------------------------------------------------
def sensor_voltage(adc_voltage):
    """
    Rechnet die am ADS1115 gemessene Spannung
    auf die ursprüngliche Sensor-Ausgangsspannung
    zurück.
    """
    # Spannungsteiler zurückrechnen
    sensor_voltage = adc_voltage * (R1 + R2) / R2
    return sensor_voltage

def moisture_percent(voltage):
    """
    Berechnet einen einfachen Feuchtigkeitswert
    von 0 bis 100 %.
    0 % = trocken
    100 % = nass
    """

    # Umrechnung:
    #
    # SENSOR_TROCKEN -> 0 %
    # SENSOR_NASS -> 100 %
    percent = (
            (SENSOR_TROCKEN - voltage)
            / (SENSOR_TROCKEN - SENSOR_NASS)
            * 100
    )

    # Auf 0...100 % begrenzen
    percent = max(0, min(100, percent))
    return percent

# ------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------
print("AZ-Delivery Hygrometer V1.2")
print("ADS1115 gestartet")
print()
try:
    while True:
        try:
            adc_value = channel.value
            adc_voltage = channel.voltage
            voltage = sensor_voltage(adc_voltage)
            moisture = moisture_percent(voltage)

            hygrometer_data = {
                # "ADC": adc_value,
                # "ADC-Spannung": round(adc_voltage, 3),
                # "Sensor": round(voltage, 3),
                "moisture": round(moisture, 1),
                "name": "hygrometer",
            }
            # A POST request to the API
            response = requests.post(
                logstash_url,
                json=hygrometer_data,
                timeout=10,
            )
            response.raise_for_status()
            # docker logs
            print(
                # f"ADC: {adc_value:5d} | "
                # f"ADC-Spannung: {adc_voltage:.3f} V | "
                # f"Sensor: {voltage:.3f} V | "
                f"Moisture: {moisture:5.1f} %"
            )
        except OSError as e:
            # z.B. I2C-Aussetzer bei loser Verkabelung - Messung überspringen statt abzustürzen
            print(f"Sensor-Fehler: {e}")
        except requests.exceptions.RequestException as e:
            # Logstash nicht erreichbar - lokale Messung trotzdem weiterlaufen lassen
            print(f"Logstash-Fehler: {e}")

        time.sleep(SENDEINTERVALL)

except KeyboardInterrupt:
    print()
    print("Programm beendet.")

finally:
    i2c.deinit()
