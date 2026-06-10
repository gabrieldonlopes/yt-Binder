from datetime import datetime,timedelta
import secrets

active_sessions = {}

def create_session() -> str:
    token = secrets.token_urlsafe(32)
    active_sessions[token] = datetime.now()
    return token

def validate_session(token: str) -> bool:
    if not token or token not in active_sessions:
        return False
    if datetime.now() - active_sessions[token] > timedelta(seconds=3600):
        del active_sessions[token]
        return False
    return True

def delete_session(token: str):
    if token in active_sessions:
        del active_sessions[token]