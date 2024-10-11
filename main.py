from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
import PyPDF2
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

def extrair_texto_de_pdf(arquivo_pdf):
    leitor_pdf = PyPDF2.PdfReader(arquivo_pdf)
    texto_extraido = ""
    for pagina in leitor_pdf.pages:
        texto = pagina.extract_text()
        if texto:
            texto_extraido += texto
    return texto_extraido

@app.post("/resumir_pdf", response_model=RespostaResumo)
async def resumir_pdf(file: UploadFile = File(...)):
    texto_pdf = extrair_texto_de_pdf(file.file)
    
    if not texto_pdf:
        raise HTTPException(status_code=400, detail="Falha ao extrair texto do PDF.")
    
    try:
        modelo = genai.GenerativeModel(model_name="gemini-1.5-flash")
        prompt = f"Resuma o seguinte texto:\n\n{texto_pdf}"
        resposta = modelo.generate_content(prompt)
        
        return {"resumo": resposta.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar o resumo: {str(e)}")

@app.post("/gerar_conteudo", response_model=RespostaResumo)
async def gerar_conteudo(prompt: str):
    try:
        modelo = genai.GenerativeModel(model_name="gemini-1.5-flash")
        resposta = modelo.generate_content(prompt)
        
        return {"resumo": resposta.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar conteúdo: {str(e)}")

@app.post("/enviar_arquivo", response_model=RespostaResumo)
async def enviar_arquivo(file: UploadFile = File(...)):
    try:
        texto_pdf = extrair_texto_de_pdf(file.file)
        if not texto_pdf:
            raise HTTPException(status_code=400, detail="Nenhum texto extraído do PDF.")
        
        modelo = genai.GenerativeModel(model_name="gemini-1.5-flash")
        prompt = f"Resuma o seguinte texto:\n\n{texto_pdf}"
        resposta = modelo.generate_content(prompt)

        return {"resumo": resposta.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo: {str(e)}")
