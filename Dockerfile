FROM python:3.13-slim

# evitar archivos .pyc y forzar log en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# dependencias del sistema (solo lo necesario para compilar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    ca-certificates \
    sudo \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root con permisos de sudo (necesario para devcontainer)
RUN adduser --disabled-password --gecos '' appuser \
    && usermod -aG sudo appuser \
    && echo 'appuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# el codigo queda de solo lectura para appuser; solo logs/ es escribible
RUN mkdir -p /code/logs && chown appuser:appuser /code/logs

USER appuser

# Crear virtual environment
RUN python -m venv /home/appuser/venv
ENV PATH="/home/appuser/venv/bin:$PATH"

# instalar dependencias de Python en el venv
COPY --chown=appuser:appuser requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# el codigo se sincroniza via Docker Compose (volumes), 
# pero copiamos para que la imagen sea funcional por si sola
COPY --chown=appuser:appuser . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
