#!/usr/bin/env python3

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
import time
from adafruit_ads1x15.analog_in import AnalogIn

# ------------------------------------------------------------
# Einstellungen
# ------------------------------------------------------------

MESSINTERVALL = 2.0  # Sekunden

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
def sensor_voltage():
    """
    Liest die Spannung am ADS1115 aus und rechnet
    sie auf die ursprüngliche Sensor-Ausgangsspannung
    zurück.
    """
    adc_voltage = channel.voltage
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
        voltage = sensor_voltage()
        moisture = moisture_percent(voltage)
        print(
            f"ADC: {channel.value:5d} | "
            f"ADC-Spannung: {channel.voltage:.3f} V | "
            f"Sensor: {voltage:.3f} V | "
            f"Feuchtigkeit: {moisture:5.1f} %"
        )
        time.sleep(MESSINTERVALL)

except KeyboardInterrupt:
    print()
    print("Programm beendet.")
