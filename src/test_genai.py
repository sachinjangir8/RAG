from llm import GeminiLLM
from google import genai
import sys

llm = GeminiLLM()
try:
    llm.client.models.generate_content(
        model="gemini-1.5-flash",
        contents="hi"
    )
except Exception as e:
    print(repr(e))
    sys.exit(1)
