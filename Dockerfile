FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim AS runtime

RUN useradd --create-home --shell /bin/bash mta
WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

COPY alembic.ini ./
COPY alembic ./alembic
COPY config ./config
COPY app.py ./

USER mta
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["morning-trading-agent"]
CMD ["run-morning-job"]
