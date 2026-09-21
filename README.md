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
   points (`SENSOR_DRY`, `SENSOR_WET`), clamped to the 0–100 range.
4. Every `ticktack` seconds (default: 5 minutes), the moisture reading is
   POSTed as JSON to the Logstash endpoint.
5. I2C errors and failed HTTP requests are logged and skipped so the loop
   keeps running instead of crashing.

## Hardware

- Raspberry Pi (or similar) with I2C enabled
- ADS1115 ADC breakout
- AZ-Delivery capacitive soil moisture sensor
- Voltage divider: R1 = 10 kΩ (AOUT → ADC), R2 = 20 kΩ (ADC → GND)

## Configuration

| Setting | Source | Purpose |
|---|---|---|
| Logstash URL | `LOGSTASH_URL` env var, or `--logstash-url` CLI arg (overrides env var) | HTTP endpoint the JSON payload is sent to. Default: `http://logstash:5044` |
| `ticktack` | constant in `src/main.py` | Measurement/send interval in seconds (default 300) |
| `R1`, `R2` | constants in `src/main.py` | Voltage divider resistor values (Ω) |
| `SENSOR_DRY` | constant in `src/main.py` | Sensor voltage at 0 % (dry) moisture |
| `SENSOR_WET` | constant in `src/main.py` | Sensor voltage at 100 % (wet) moisture |

Calibrate `SENSOR_DRY`/`SENSOR_WET` for your specific sensor.

## Running

### Docker

```bash
cd src
docker build -t apws-hygrometer .
docker run --device /dev/i2c-1 -e LOGSTASH_URL=http://logstash:5044 apws-hygrometer
```

The image is based on `uv` + Python 3.12 and installs
`adafruit-circuitpython-ads1x15`, `lgpio`, and `requests`.

### Locally

```bash
uv add adafruit-circuitpython-ads1x15 lgpio requests
uv run src/main.py --logstash-url http://logstash:5044
```

Requires I2C access to the ADS1115 (e.g. run on a Raspberry Pi with I2C
enabled).

## Output

Each cycle logs the current ADC/voltage/moisture readings to stdout and
sends:

```json
{ "moisture": 42.3 }
```

## License

MIT, see [LICENSE](LICENSE).
