#FROM dustynv/pytorch:2.4-r36.4.0-cu128-24.04
#FROM dustynv/l4t-pytorch:r36.4.0
FROM dustynv/l4t-ml:r36.4.0 AS stage1

RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

FROM stage1 AS stage2

RUN pip3 install --no-cache-dir ultralytics --no-deps --index-url https://pypi.org/simple

FROM stage2 AS stage3

RUN pip3 install --no-cache-dir --verbose --index-url https://pypi.org/simple \
  PyYAML \
  blinker \
  pyserial \
  numpy \
  asyncio-atexit \
  adafruit-circuitpython-bno055 \
  click \
  nicegui



RUN  npm install -g @anthropic-ai/claude-code


WORKDIR /vega

