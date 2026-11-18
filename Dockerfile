FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.9
COPY pyproject.toml uv.lock ./
COPY booking_agent ./booking_agent
COPY coordinator ./coordinator
COPY eval_agent ./eval_agent
RUN uv sync --locked --no-dev
RUN useradd --create-home booking && mkdir -p /app/runtime && chown -R booking:booking /app
USER booking
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8001
CMD ["uvicorn", "booking_agent.server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
