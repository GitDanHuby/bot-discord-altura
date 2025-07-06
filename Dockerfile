# Usa uma imagem oficial do Python como base
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala as dependências de sistema (a parte mais importante)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus-dev \
    brotli \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências do Python
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código do bot
COPY . .

# Define o comando para iniciar o bot
CMD ["python", "main.py"]
