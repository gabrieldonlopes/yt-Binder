from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

import yt_dlp
import os 

from logs import LoggerForDownload
from downloader import download_youtube_video

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'cookiesfrombrowser': ('firefox',), 
    'logger':LoggerForDownload(),
    'js_runtimes': {'node': {}},
    'remote_components': ['ejs:github'],
    'quiet': True
}

# Inicializa o app FastAPI e o Jinja
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/logs")
async def ler_logs():
    """Lê as últimas 50 linhas do arquivo de log."""

    if not os.path.exists("download_videos.log"):
        return {"logs": "Aguardando início dos processos..."}
    
    with open("download_videos.log", "r") as f:
        linhas = f.readlines()
        # Retorna apenas as últimas 50 linhas para não pesar o navegador
        return {"logs": "".join(linhas[-50:])}

@app.get("/")
async def pagina_inicial(request: Request):
    """Renderiza a página HTML inicial."""

    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

@app.get("/info")
async def obter_informacoes(url: str):
    """Extrai os metadados do vídeo sem fazer o download."""
    opts_info = {'quiet': True, 'extract_flat': False} 
    try:
        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            return {"title": info.get("title"), "thumbnail": info.get("thumbnail")}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/download")
async def processar_download(
    request: Request, 
    background_tasks: BackgroundTasks,
    url: str = Form(...), 
    media_type: str = Form(...), 
    quality: str = Form(...)
):
    """Recebe os dados do formulário e envia o download para background."""
    
    background_tasks.add_task(download_youtube_video,url,ydl_opts)
    
    mensagem_sucesso = f"Download de {url} adicionado à fila! Verifique o arquivo de log."
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"mensagem": mensagem_sucesso}
    )