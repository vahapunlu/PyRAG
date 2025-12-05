import chromadb
from llama_index.embeddings.openai import OpenAIEmbedding
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI embedding
embed_model = OpenAIEmbedding(
    model="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY")
)

# ChromaDB
client = chromadb.PersistentClient('./chroma_db')
col = client.get_collection('LDA')

# Test query
query = "cable cross-sections electrical wiring"
print(f"Query: {query}\n")

# Get embedding
query_embedding = embed_model.get_query_embedding(query)
print(f"Query embedding dimension: {len(query_embedding)}\n")

# Search
results = col.query(
    query_embeddings=[query_embedding],
    n_results=3
)

print(f"Found {len(results['documents'][0])} results:\n")

for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
    similarity = 1 - distance  # Convert distance to similarity
    print(f"--- Result {i+1} (Similarity: {similarity:.3f}) ---")
    print(doc[:400])
    print()
