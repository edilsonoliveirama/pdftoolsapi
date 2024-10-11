# Use uma imagem oficial do Python como base
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie o arquivo requirements.txt para o container
COPY requirements.txt .

# Instale as dependências Python no container
RUN pip install --no-cache-dir -r requirements.txt

# Copie o código da aplicação para o container
COPY . .

# Copie o arquivo .env para o container
COPY .env .env

# Exponha a porta 8000 para que o Uvicorn possa ser acessado externamente
EXPOSE 8000

# Defina o comando padrão para rodar o Uvicorn e iniciar o servidor FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
