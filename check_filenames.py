import chromadb
from chromadb.config import Settings as ChromaSettings

client = chromadb.PersistentClient(
    path='./chroma_db',
    settings=ChromaSettings(anonymized_telemetry=False)
)

collection = client.get_collection('engineering_standards')
total_count = collection.count()
print(f"Toplam kayıt sayısı: {total_count}\n")
results = collection.get(limit=total_count, include=['metadatas'])

print("=== VERITABANINDAKI DOSYA ADLARI ===\n")

# Count how many have each field
file_name_count = 0
doc_name_count = 0
file_names = set()
doc_names = set()

for metadata in results['metadatas']:
    fn = metadata.get('file_name')
    dn = metadata.get('document_name')
    
    if fn and fn != 'Unknown':
        file_name_count += 1
        file_names.add(fn)
    
    if dn and dn != 'Unknown':
        doc_name_count += 1
        doc_names.add(dn)

print(f"FILE_NAME field: {file_name_count}/{total_count} kayıtta dolu")
for i, fn in enumerate(sorted(file_names), 1):
    print(f"  {i}. {fn}")

print(f"\nDOCUMENT_NAME field: {doc_name_count}/{total_count} kayıtta dolu")
for i, dn in enumerate(sorted(doc_names), 1):
    print(f"  {i}. {dn}")
