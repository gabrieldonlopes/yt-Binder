import os
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ADMIN_USER = os.getenv("APP_USERNAME")
ADMIN_PASS = os.getenv("APP_PASSWORD")

@router.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request):
    """Renderiza a página de login."""
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
async def processar_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Verifica as credenciais e cria o cookie de sessão."""
    if username == ADMIN_USER and password == ADMIN_PASS:
        # Credenciais corretas: Redireciona para a home (/)
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        # Seta um cookie simples no navegador para lembrar que o usuário está logado
        response.set_cookie(key="sessao_yt_binder", value="autenticado", httponly=True)
        return response
    else:
        # Credenciais incorretas: Recarrega a página com erro
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"erro": "Usuário ou senha incorretos!"}
        )

@router.get("/logout")
async def logout():
    """Remove o cookie e desloga o usuário."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("sessao_yt_binder")
    return response