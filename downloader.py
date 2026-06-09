import yt_dlp
from logs import LoggerForDownload
ydl_opts = {
    # baixando vídeo e áudio na melhor qualidade
    'format': 'bestvideo+bestaudio/best',
    
    # utilizando formato mp4 como output
    'merge_output_format': 'mp4',
    
    # utilizando cookies e firefox
    'cookiesfrombrowser': ('firefox',), 
    
    # logger
    'logger':LoggerForDownload(),

    # CORREÇÃO AQUI: A chave correta é 'js_runtimes'
    'js_runtimes': {'node': {}},

    # script necessário para baixar vídeos
    'remote_components': ['ejs:github'],

    'quiet': True
}

def download_youtube_video(url:str):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    

if __name__ == "__main__":
    download_youtube_video('https://www.youtube.com/watch?v=C0DPdy98e4c')