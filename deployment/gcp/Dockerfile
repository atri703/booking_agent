FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.9

COPY pyproject.toml uv.lock ./
COPY booking_agent ./booking_agent
COPY coordinator ./coordinator
COPY eval_agent ./eval_agent
RUN uv sync --locked --no-dev

RUN useradd --create-home booking \
    && mkdir -p /tmp/booking-agent \
    && chown -R booking:booking /app /tmp/booking-agent

USER booking
ENV PATH="/app/.venv/bin:$PATH"
ENV BOOKING_DATA_DIR="/tmp/booking-agent"

EXPOSE 8080
CMD ["uvicorn", "booking_agent.server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
