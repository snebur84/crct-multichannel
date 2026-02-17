# Usa uma imagem leve do Python
FROM python:3.10-slim

# Instala bibliotecas do sistema para conectar no Postgres
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala as dependências diretamente
# Adicionamos pydantic explicitamente para evitar erros na validação dos ramais
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    pydantic \
    python-multipart \
    panoramisk

# Copia todo o conteúdo da pasta backend para o /app do container
COPY . .

# Comando para rodar a API
# O "--reload" é opcional, mas útil se você estiver em desenvolvimento
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
