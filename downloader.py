import yt_dlp
from urllib.parse import urlparse
import ipaddress

ALLOWED_DOMAINS = {
    'youtube.com', 'www.youtube.com', 'youtu.be', 
    'm.youtube.com', 'music.youtube.com'
}

def validate_youtube_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        
        # Verificar esquema
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Verificar domínio
        domain = parsed.netloc.lower()
        if not any(domain == allowed or domain.endswith('.' + allowed) for allowed in ALLOWED_DOMAINS):
            return False
        
        # Verificar se não é IP privado
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            pass  # É um domínio, não IP
        
        return True
    except Exception:
        return False


def download_youtube_video(url:str, ydl_opts:dict):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    