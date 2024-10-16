from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import google.generativeai as genai
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from dotenv import load_dotenv
import tempfile

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

class RespostaPadrao(BaseModel):
    message: str
    file_path: str = None

# Função para obter o modelo Generative AI
def obter_modelo_genai():
    return genai.GenerativeModel(model_name="gemini-1.5-flash")

# Extrair texto de PDF
def extrair_texto_de_pdf(arquivo_pdf):
    leitor_pdf = PdfReader(arquivo_pdf)
    texto_extraido = []
    for pagina in leitor_pdf.pages:
        texto = pagina.extract_text()
        if texto:
            texto_extraido.append(texto)
    return ''.join(texto_extraido)

# Função para salvar PDF temporariamente
def salvar_pdf_temp(writer: PdfWriter):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    writer.write(temp_file)
    temp_file.close()
    return temp_file.name

# Endpoint para resumir PDF
@app.post("/resumir_pdf", response_model=RespostaResumo)
async def resumir_pdf(file: UploadFile = File(...)):
    texto_pdf = extrair_texto_de_pdf(file.file)
    
    if not texto_pdf:
        raise HTTPException(status_code=400, detail="Falha ao extrair texto do PDF.")
    
    try:
        modelo = obter_modelo_genai()
        # Limitar o texto para evitar excesso de dados no prompt
        MAX_CHARS = 1000
        prompt = f"Resuma o seguinte texto:\n\n{texto_pdf[:MAX_CHARS]}"
        resposta = modelo.generate_content(prompt)
        
        return {"resumo": resposta.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar o resumo: {str(e)}")

# Endpoint para gerar conteúdo a partir de um prompt
@app.post("/gerar_conteudo", response_model=RespostaResumo)
async def gerar_conteudo(prompt: str):
    try:
        modelo = obter_modelo_genai()
        resposta = modelo.generate_content(prompt)
        
        return {"resumo": resposta.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar conteúdo: {str(e)}")

# Endpoint para mesclar PDFs
@app.post("/mesclar_pdfs", response_model=RespostaPadrao)
async def mesclar_pdfs(files: list[UploadFile] = File(...)):
    merger = PdfMerger()

    for pdf in files:
        merger.append(pdf.file)

    merged_pdf_path = salvar_pdf_temp(merger)

    return RespostaPadrao(message="PDFs mesclados com sucesso", file_path=merged_pdf_path)

# Endpoint para dividir PDF
@app.post("/dividir_pdf", response_model=RespostaPadrao)
async def dividir_pdf(file: UploadFile = File(...), start_page: int = 0, end_page: int = 1):
    reader = PdfReader(file.file)
    
    # Validar se o intervalo de páginas é válido
    if start_page < 0 or end_page >= len(reader.pages):
        raise HTTPException(status_code=400, detail="Intervalo de páginas fora dos limites do documento.")

    writer = PdfWriter()

    for i in range(start_page, end_page + 1):
        writer.add_page(reader.pages[i])

    split_pdf_path = salvar_pdf_temp(writer)

    return RespostaPadrao(message="PDF dividido com sucesso", file_path=split_pdf_path)

# Endpoint para rotacionar PDF
@app.post("/rotacionar_pdf", response_model=RespostaPadrao)
async def rotacionar_pdf(file: UploadFile = File(...), rotation: int = 90):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate_clockwise(rotation)
        writer.add_page(page)

    rotated_pdf_path = salvar_pdf_temp(writer)

    return RespostaPadrao(message="PDF rotacionado com sucesso", file_path=rotated_pdf_path)

# Endpoint para adicionar marca d'água
@app.post("/adicionar_marca_dagua", response_model=RespostaPadrao)
async def adicionar_marca_dagua(file: UploadFile = File(...), watermark_file: UploadFile = File(...)):
    try:
        # Verificar se os arquivos enviados são PDFs válidos
        reader = PdfReader(file.file)
        watermark_reader = PdfReader(watermark_file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler o arquivo PDF: {str(e)}")

    writer = PdfWriter()
    watermark_page = watermark_reader.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    watermarked_pdf_path = salvar_pdf_temp(writer)

    return RespostaPadrao(message="Marca d'água adicionada com sucesso", file_path=watermarked_pdf_path)

# Endpoint para proteger PDF com senha e permitir nome personalizado
@app.post("/proteger_pdf", response_model=RespostaPadrao)
async def proteger_pdf(file: UploadFile = File(...), senha: str = "1234", nome_saida: str = None):
    reader = PdfReader(file.file)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Criptografar com senha
    writer.encrypt(senha)
    
    # Garante que o nome de saída termine com .pdf
    if not nome_saida:
        nome_saida = f"protected_{file.filename}"
    elif not nome_saida.endswith(".pdf"):
        nome_saida += ".pdf"

    encrypted_pdf_path = salvar_pdf_temp(writer)

    return RespostaPadrao(message="PDF protegido com sucesso", file_path=encrypted_pdf_path)

# Endpoint GET para baixar o PDF protegido
@app.get("/baixar_protected_pdf/{file_name}")
async def baixar_protected_pdf(file_name: str):
    pdf_path = f"/app/{file_name}"

    # Verificar se o arquivo existe e prevenir Path Traversal
    if not os.path.exists(pdf_path) or not os.path.basename(pdf_path) == file_name:
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    
    # Retornar o PDF para download
    return FileResponse(pdf_path, media_type="application/pdf", filename=file_name)
