from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import google.generativeai as genai
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
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

# Extrair texto de PDF
def extrair_texto_de_pdf(arquivo_pdf):
    leitor_pdf = PdfReader(arquivo_pdf)
    texto_extraido = ""
    for pagina in leitor_pdf.pages:
        texto = pagina.extract_text()
        if texto:
            texto_extraido += texto
    return texto_extraido

# Endpoint para resumir PDF
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

# Endpoint para gerar conteúdo a partir de um prompt
@app.post("/gerar_conteudo", response_model=RespostaResumo)
async def gerar_conteudo(prompt: str):
    try:
        modelo = genai.GenerativeModel(model_name="gemini-1.5-flash")
        resposta = modelo.generate_content(prompt)
        
        return {"resumo": resposta.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar conteúdo: {str(e)}")

# Função para salvar PDF
def salvar_pdf(writer: PdfWriter, output_path: str):
    with open(output_path, "wb") as f:
        writer.write(f)

# Endpoint para mesclar PDFs
@app.post("/mesclar_pdfs")
async def mesclar_pdfs(files: list[UploadFile] = File(...)):
    merger = PdfMerger()

    for pdf in files:
        merger.append(pdf.file)

    merged_pdf_path = "/app/merged.pdf"
    with open(merged_pdf_path, "wb") as f:
        merger.write(f)

    return {"message": "PDFs mesclados com sucesso", "file_path": merged_pdf_path}

# Endpoint para dividir PDF
@app.post("/dividir_pdf")
async def dividir_pdf(file: UploadFile = File(...), start_page: int = 0, end_page: int = 1):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    for i in range(start_page, end_page + 1):
        writer.add_page(reader.pages[i])

    split_pdf_path = "/app/split.pdf"
    salvar_pdf(writer, split_pdf_path)

    return {"message": "PDF dividido com sucesso", "file_path": split_pdf_path}

# Endpoint para rotacionar PDF
@app.post("/rotacionar_pdf")
async def rotacionar_pdf(file: UploadFile = File(...), rotation: int = 90):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate_clockwise(rotation)
        writer.add_page(page)

    rotated_pdf_path = "/app/rotated.pdf"
    salvar_pdf(writer, rotated_pdf_path)

    return {"message": "PDF rotacionado com sucesso", "file_path": rotated_pdf_path}

# Endpoint para adicionar marca d'água
@app.post("/adicionar_marca_dagua")
async def adicionar_marca_dagua(file: UploadFile = File(...), watermark_file: UploadFile = File(...)):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    watermark_reader = PdfReader(watermark_file.file)
    watermark_page = watermark_reader.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    watermarked_pdf_path = "/app/watermarked.pdf"
    salvar_pdf(writer, watermarked_pdf_path)

    return {"message": "Marca d'água adicionada com sucesso", "file_path": watermarked_pdf_path}

# Endpoint para proteger PDF com senha e permitir nome personalizado
@app.post("/proteger_pdf")
async def proteger_pdf(file: UploadFile = File(...), senha: str = "1234", nome_saida: str = None):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Criptografar com senha
    if not nome_saida:
        # Se o nome de saída não for fornecido, use o nome original do arquivo com "protected_" prefixado
        nome_saida = f"protected_{file.filename}"
    else:
        # Garante que o nome de saída termine com .pdf
        if not nome_saida.endswith(".pdf"):
            nome_saida += ".pdf"

    encrypted_pdf_path = f"/app/{nome_saida}"

    # Salvar o PDF protegido
    salvar_pdf(writer, encrypted_pdf_path)

    # Retornar uma mensagem informando que o PDF foi protegido
    return {"message": "PDF protegido com sucesso.", "protected_pdf": encrypted_pdf_path}

# Endpoint GET para baixar o PDF protegido
@app.get("/baixar_protected_pdf/{file_name}")
async def baixar_protected_pdf(file_name: str):
    pdf_path = f"/app/{file_name}"

    # Verificar se o arquivo existe
    if os.path.exists(pdf_path):
        # Retornar o PDF para download
        return FileResponse(pdf_path, media_type="application/pdf", filename=file_name)
    else:
        # Retornar erro se o PDF não for encontrado
        raise HTTPException(status_code=404, detail="PDF não encontrado")
