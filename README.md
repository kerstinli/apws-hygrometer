# APWS Hygrometer

A small Python service that reads soil moisture from an AZ-Delivery capacitive
hygrometer via an ADS1115 ADC (I2C) and periodically ships the reading to
Logstash as JSON over HTTP.

## How it works

1. The sensor's analog output is read through a voltage divider (R1/R2) into
   channel A0 of an ADS1115 16-bit ADC.
2. The measured ADC voltage is scaled back to the sensor's original output
   voltage.
3. That voltage is mapped to a 0–100 % moisture value using two calibration
   points (`SENSOR_TROCKEN` = dry, `SENSOR_NASS` = wet), clamped to the
   0–100 range.
4. Every `SENDEINTERVALL` seconds (default: 5 minutes), the moisture reading
   is POSTed as JSON to `logstash_url`.
5. I2C errors and failed HTTP requests are logged and skipped so the loop
   keeps running instead of crashing.

## Hardware

- Raspberry Pi (or similar) with I2C enabled
- ADS1115 ADC breakout
- AZ-Delivery capacitive soil moisture sensor
- Voltage divider: R1 = 10 kΩ (AOUT → ADC), R2 = 20 kΩ (ADC → GND)

## Configuration

All configuration is done via constants at the top of `src/main.py`:

| Constant | Purpose |
|---|---|
| `logstash_url` | HTTP endpoint the JSON payload is sent to |
| `SENDEINTERVALL` | Measurement/send interval in seconds |
| `R1`, `R2` | Voltage divider resistor values (Ω) |
| `SENSOR_TROCKEN` | Sensor voltage at 0 % (dry) moisture |
| `SENSOR_NASS` | Sensor voltage at 100 % (wet) moisture |

Calibrate `SENSOR_TROCKEN`/`SENSOR_NASS` for your specific sensor.

## Running

### Docker

```bash
cd src
docker build -t apws-hygrometer .
docker run --device /dev/i2c-1 apws-hygrometer
```

The image is based on `uv` + Python 3.12 and installs
`adafruit-circuitpython-ads1x15`, `lgpio`, and `requests`.

### Locally

```bash
uv add adafruit-circuitpython-ads1x15 lgpio requests
uv run src/main.py
```

Requires I2C access to the ADS1115 (e.g. run on a Raspberry Pi with I2C
enabled).

## Output

Each cycle prints the current moisture reading to stdout and sends:

```json
{ "moisture": 42.3 }
```

## License

MIT, see [LICENSE](LICENSE).
