from dotenv import load_dotenv
import os

load_dotenv()

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN", "")
SECRET = os.getenv("SECRET", "mysecret123")
EMAIL = os.getenv("EMAIL", "you@example.com")
GLOBAL_TIMEOUT = int(os.getenv("GLOBAL_TIMEOUT", "170"))
DOWNLOAD_MAX_BYTES = int(os.getenv("DOWNLOAD_MAX_BYTES", "52428800"))
