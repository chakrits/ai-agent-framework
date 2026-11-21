FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY orchestrator/requirements.txt /app/orchestrator/requirements.txt
RUN pip install --no-cache-dir -r /app/orchestrator/requirements.txt

COPY version.txt /app/version.txt
COPY AGENTS.md /app/AGENTS.md
COPY .agents /app/.agents
COPY docs/operating-model /app/docs/operating-model
COPY docs/contracts /app/docs/contracts
COPY examples/project-packs /app/examples/project-packs
COPY orchestrator /app/orchestrator

RUN useradd --create-home --shell /usr/sbin/nologin sdlc \
    && mkdir -p /app/.sdlc/runs /app/.sdlc/telemetry \
    && chown -R sdlc:sdlc /app/.sdlc

USER sdlc
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "orchestrator.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
