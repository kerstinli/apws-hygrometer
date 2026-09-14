# Basis-Image
FROM ghcr.io/astral-sh/uv:0.12-python3.12-trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends i2c-tools

WORKDIR  /hygrometer

RUN uv init

RUN uv add adafruit-circuitpython-ads1x15 lgpio

COPY main.py .

CMD ["uv", "run", "main.py"]