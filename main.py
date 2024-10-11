from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse  # Adicionei esta linha
from pydantic import BaseModel
import os
import google.generativeai as genai
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = FastAPI()

# Obter a chave da API do arquivo .env
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("A variável de ambiente API_KEY não está configurada.")

# Configurar a chave da API para a biblioteca Google Generative AI
genai.configure(api_key=API_KEY)

class RespostaResumo(BaseModel):
    resumo: str

# Função para salvar PDF
def salvar_pdf(writer: PdfWriter, output_path: str):
    with open(output_path, "wb") as f:
        writer.write(f)

# Endpoint para proteger PDF com senha
@app.post("/proteger_pdf")
async def proteger_pdf(file: UploadFile = File(...), senha: str = "1234"):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Criptografar com senha
    writer.encrypt(senha)

    encrypted_pdf_path = "/app/encrypted.pdf"
    salvar_pdf(writer, encrypted_pdf_path)

    # Retornar o arquivo para download
    return FileResponse(encrypted_pdf_path, media_type='application/pdf', filename="encrypted.pdf")
