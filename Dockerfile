FROM python:3.13-slim

# evitar archivos .pyc y forzar log en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# dependencias del sistema (Limpiado para Postgres y Git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# instalar dependencias de Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# el codigo se sincroniza via Docker Compose (volumes), 
# pero copiamos para que la imagen sea funcional por si sola
COPY . .

EXPOSE 8000

# Crear usuario no-root con permisos de sudo
RUN adduser --disabled-password --gecos '' appuser \
    && usermod -aG sudo appuser \
    && echo 'appuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers \
    && chown -R appuser:appuser /code

USER appuser

CMD ["python", "run.py"]
