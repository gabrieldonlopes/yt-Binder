import os
import secrets 

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta

from sessions import create_session, delete_session

SESSION_EXPIRY = 3600
router = APIRouter()
templates = Jinja2Templates(directory="templates")
active_sessions = {}

ADMIN_USER = os.getenv("APP_USERNAME")
ADMIN_PASS = os.getenv("APP_PASSWORD")

@router.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
async def processar_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if secrets.compare_digest(username, ADMIN_USER or "") and secrets.compare_digest(password, ADMIN_PASS or ""):
        session_token = create_session() 
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,  # Obrigatório para HTTPS na internet
            samesite="lax",
            max_age=SESSION_EXPIRY
        )
        return response
        
    # Se falhar, renderiza novamente com mensagem de erro
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"erro": "Usuário ou senha incorretos."}
    )

@router.get("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        delete_session(session_token)
    
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_token")
    return response