import sys
from qdrant_client import QdrantClient
try:
    print("Connecting to Qdrant...")
    client = QdrantClient(host="localhost", port=6333, timeout=3)
    collections = client.get_collections()
    print("Collections:", collections)
except Exception as e:
    print("Qdrant error:", e)
    sys.exit(1)
