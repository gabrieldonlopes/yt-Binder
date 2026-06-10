import os 
import yt_dlp
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse

# Suas importações modulares
from logs import LoggerForDownload
from downloader import download_youtube_video

# Importa a router de autenticação
from auth import router as auth_router

# Carrega as variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DO DIRETÓRIO DE DOWNLOAD ---
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")
os.makedirs(DOWNLOAD_PATH, exist_ok=True) # Cria a pasta se não existir

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    #'cookiesfrombrowser': ('firefox',), 
    'cookiefile': '/app/youtube_cookies.txt',
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

# --- SISTEMA DE PROTEÇÃO ---
def verificar_sessao(request: Request):
    cookie = request.cookies.get("sessao_yt_binder")
    if cookie != "autenticado":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado. Faça login.")
    return True

# --- ROTAS DA INTERFACE ---
@app.get("/")
async def pagina_inicial(request: Request):
    if request.cookies.get("sessao_yt_binder") != "autenticado":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/logs", dependencies=[Depends(verificar_sessao)])
async def ler_logs():
    if not os.path.exists("download_videos.log"):
        return {"logs": "Aguardando início dos processos..."}
    with open("download_videos.log", "r") as f:
        linhas = f.readlines()
        return {"logs": "".join(linhas[-50:])}
    
@app.get("/info", dependencies=[Depends(verificar_sessao)])
async def obter_informacoes(url: str):
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
    background_tasks.add_task(download_youtube_video, url, ydl_opts)
    mensagem_sucesso = f"Download adicionado à fila! Verifique o terminal de logs."
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