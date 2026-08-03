import time

start = time.time()

print("Before import")

from app.services.embedder import embed_chunks

print("After import:", time.time() - start)