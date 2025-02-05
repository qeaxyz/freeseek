import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LOG_DETAILED = os.getenv('FREESEEK_LOG_DETAILED', 'True').lower() == 'true'
    API_KEY = os.getenv('FREESEEK_API_KEY')
    BASE_URL = os.getenv('FREESEEK_BASE_URL', 'https://api.freeseek.com/v1')
    TIMEOUT = int(os.getenv('FREESEEK_TIMEOUT', 30))
    MAX_RETRIES = int(os.getenv('FREESEEK_MAX_RETRIES', 3))
    BACKOFF_FACTOR = int(os.getenv('FREESEEK_BACKOFF_FACTOR', 1))