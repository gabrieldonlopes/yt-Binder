import os 
import yt_dlp
import secrets
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse

# Suas importações modulares
from logs import LoggerForDownload
from downloader import download_youtube_video,validate_youtube_url

# Importa a router de autenticação
from auth import router as auth_router
from sessions import validate_session

# Carrega as variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DO DIRETÓRIO DE DOWNLOAD ---
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")
os.makedirs(DOWNLOAD_PATH, exist_ok=True) # Cria a pasta se não existir

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'cookiesfrombrowser': ('firefox',), 
    #'cookiefile': '/app/youtube_cookies.txt',
    'logger': LoggerForDownload(),
    'js_runtimes': {'node': {}},
    'remote_components': ['ejs:github'],
    'quiet': True,
    # NOVA CONFIGURAÇÃO: Define o template de saída para a pasta escolhida
    'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s')
}

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)

def verificar_sessao(request: Request):
    session_token = request.cookies.get("session_token")
    if not validate_session(session_token):
        raise HTTPException(status_code=401, detail="Não autenticado")
    return True

# --- ROTAS DA INTERFACE ---
@app.get("/")
async def pagina_inicial(request: Request):
    try:
        verificar_sessao(request)
        return templates.TemplateResponse(request=request, name="index.html")
    except HTTPException:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/logs", dependencies=[Depends(verificar_sessao)])
async def ler_logs():
    if not os.path.exists("download_videos.log"):
        return {"logs": "Aguardando início dos processos..."}
    with open("download_videos.log", "r") as f:
        linhas = f.readlines()
        return {"logs": "".join(linhas[-50:])}
    
@app.get("/info", dependencies=[Depends(verificar_sessao)])
async def obter_informacoes(url: str):
    if not validate_youtube_url(url):
        raise HTTPException(status_code=400, detail="URL inválida ou não permitida")
    
    opts_info = {'quiet': True, 'extract_flat': False} 
    try:
        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            return {"title": info.get("title"), "thumbnail": info.get("thumbnail")}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/download", dependencies=[Depends(verificar_sessao)])
async def processar_download(
    request: Request, 
    background_tasks: BackgroundTasks,
    url: str = Form(...), 
    media_type: str = Form(...), 
    quality: str = Form(...)
):
    if not validate_youtube_url(url):
        raise HTTPException(status_code=400, detail="URL inválida ou não permitida")

    background_tasks.add_task(download_youtube_video, url, ydl_opts)
    mensagem_sucesso = f"Download adicionado à fila!"
    return {"status": "success", "message": mensagem_sucesso}

# --- NOVAS ROTAS DE GERENCIAMENTO DE ARQUIVOS ---
@app.get("/arquivos", dependencies=[Depends(verificar_sessao)])
async def listar_arquivos():
    """Lista todos os arquivos mp4 presentes na pasta de download do servidor."""
    arquivos = []
    if os.path.exists(DOWNLOAD_PATH):
        for f in os.listdir(DOWNLOAD_PATH):
            if os.path.isfile(os.path.join(DOWNLOAD_PATH, f)) and f.endswith('.mp4'):
                arquivos.append(f)
    return {"arquivos": sorted(arquivos)}

@app.get("/baixar/{nome_arquivo}", dependencies=[Depends(verificar_sessao)])
async def enviar_arquivo_cliente(nome_arquivo: str):
    """Envia o arquivo do servidor para o computador do cliente."""
    # Proteção básica contra path traversal (tentativa de acessar pastas acima)
    if "/" in nome_arquivo or "\\" in nome_arquivo or ".." in nome_arquivo:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    caminho_arquivo = os.path.join(DOWNLOAD_PATH, nome_arquivo)
    
    if not os.path.exists(caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor.")
        
    # Retorna o arquivo como um anexo para forçar o download no navegador
    return FileResponse(
        path=caminho_arquivo, 
        filename=nome_arquivo, 
        media_type='application/octet-stream'
    )