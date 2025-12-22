FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN uv sync --frozen --no-cache

CMD ["/app/.venv/bin/python", "src/agent_mcp/server.py", "--port", "9090", "--host", "0.0.0.0", "--transport", "streamable-http"]
