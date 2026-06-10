from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates

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


@app.get("/")
async def pagina_inicial(request: Request):
    """Renderiza a página HTML inicial."""

    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )


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