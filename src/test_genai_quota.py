from google import genai
from config import get_settings
import sys

settings = get_settings()
try:
    print("Testing gemini again...")
    client = genai.Client(api_key=settings.gemini_api_key)
    res = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="hi"
    )
    print("SUCCESS")
except Exception as e:
    print(repr(e))
    sys.exit(1)
