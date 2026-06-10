import os 
import yt_dlp
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse

# Suas importações modulares
from logs import LoggerForDownload
from downloader import download_youtube_video

# Importa a router de autenticação que criamos
from auth import router as auth_router

# Carrega as variáveis de ambiente (como o seu usuário e senha do .env)
load_dotenv()

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'cookiesfrombrowser': ('firefox',), 
    'logger': LoggerForDownload(),
    'js_runtimes': {'node': {}},
    'remote_components': ['ejs:github'],
    'quiet': True
}

# Inicializa o app FastAPI e o Jinja
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Registra as rotas de login/logout no app principal
app.include_router(auth_router)

# --- SISTEMA DE PROTEÇÃO ---
def verificar_sessao(request: Request):
    """Verifica se o cookie existe. Se não existir, bloqueia a requisição API."""
    cookie = request.cookies.get("sessao_yt_binder")
    if cookie != "autenticado":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado. Faça login.")
    return True


@app.get("/")
async def pagina_inicial(request: Request):
    """Renderiza a página HTML inicial. Se não estiver logado, joga pro /login."""
    if request.cookies.get("sessao_yt_binder") != "autenticado":
        return RedirectResponse(url="/login")
        
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

# Note o dependencies=[Depends(verificar_sessao)] para blindar essas rotas
@app.get("/logs", dependencies=[Depends(verificar_sessao)])
async def ler_logs():
    """Lê as últimas 50 linhas do arquivo de log."""
    if not os.path.exists("download_videos.log"):
        return {"logs": "Aguardando início dos processos..."}
    
    with open("download_videos.log", "r") as f:
        linhas = f.readlines()
        # Retorna apenas as últimas 50 linhas para não pesar o navegador
        return {"logs": "".join(linhas[-50:])}
    
@app.get("/info", dependencies=[Depends(verificar_sessao)])
async def obter_informacoes(url: str):
    """Extrai os metadados do vídeo sem fazer o download."""
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
    """Recebe os dados do formulário e envia o download para background."""
    
    background_tasks.add_task(download_youtube_video, url, ydl_opts)
    
    mensagem_sucesso = f"Download adicionado à fila! Verifique o terminal de logs."
    
    # Ajustado para retornar JSON (assim o JavaScript da página consegue ler e mostrar o alerta de sucesso)
    return {"status": "success", "message": mensagem_sucesso}