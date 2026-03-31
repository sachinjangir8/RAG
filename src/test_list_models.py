from google import genai
from config import get_settings
import sys

settings = get_settings()
try:
    client = genai.Client(api_key=settings.gemini_api_key)
    models = client.models.list()
    for m in models:
        print(m.name)
except Exception as e:
    print("Error:", repr(e))
    sys.exit(1)
