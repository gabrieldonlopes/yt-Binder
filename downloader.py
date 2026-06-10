import yt_dlp
from logs import LoggerForDownload


def download_youtube_video(url:str, ydl_opts:dict):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    

if __name__ == "__main__":
    download_youtube_video('https://www.youtube.com/watch?v=C0DPdy98e4c')