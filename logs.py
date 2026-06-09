import logging

# 1. Configurar o sistema de logs nativo do Python
logging.basicConfig(
    filename='download_videos.log',      # Nome do arquivo onde os logs serão salvos
    level=logging.INFO,                  # Nível mínimo de captura (INFO, WARNING, ERROR)
    format='%(asctime)s | %(levelname)s | %(message)s', # Formato visual do log
    datefmt='%Y-%m-%d %H:%M:%S'
)

class LoggerForDownload:
    def debug(self, msg):
        # O yt-dlp envia mensagens gerais de progresso para o método 'debug'.
        # Filtramos o que é lixo técnico e logamos o resto como INFO.
        if msg.startswith('[debug] '):
            logging.debug(msg)
        else:
            logging.info(msg)

    def info(self, msg):
        logging.info(msg)

    def warning(self, msg):
        logging.warning(msg)

    def error(self, msg):
        logging.error(msg)
