import json
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from pydantic import BaseModel
import chromadb
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# Initialize ChromaDB
persist_directory = 'db/chroma'
os.makedirs(persist_directory, exist_ok=True)
client = chromadb.PersistentClient(path=persist_directory)
collection = client.get_or_create_collection(name="incident_records")

# Embedding function
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def sanitize_metadata_value(value):
    return value if value is not None else "unknown"

@app.post("/upload-json")
async def upload_json(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Invalid JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    all_chunks, all_embeddings, metadatas, ids = [], [], [], []
    skipped = 0

    for i, record in enumerate(data):
        text = record.get("error_description", "")
        if not text.strip():
            skipped += 1
            continue

        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        chunks = splitter.split_text(text)
        embeddings = [embedding_function.embed_query(c) for c in chunks]

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            all_chunks.append(chunk)
            all_embeddings.append(emb)
            metadatas.append({
                "jira_id": sanitize_metadata_value(record.get("jira_id")),
                "error_description": sanitize_metadata_value(text),
                "error_type": sanitize_metadata_value(record.get("error_type")),
                "status": sanitize_metadata_value(record.get("status")),
                "resolution_comment": sanitize_metadata_value(record.get("resolution_comment")),
                "timestamp": sanitize_metadata_value(record.get("timestamp")),
                "rca_doc_url": sanitize_metadata_value(record.get("rca_doc_url")),
                "other_metadata": sanitize_metadata_value(record.get("other_metadata")),
                "chunk_index": idx
            })
            ids.append(f"{record.get('jira_id')}_{idx}")

    try:
        collection.add(
            documents=all_chunks,
            embeddings=all_embeddings,
            metadatas=metadatas,
            ids=ids
        )
    except Exception as e:
        logger.error(f"Failed to store in ChromaDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to store data in ChromaDB")

    return {
        "message": f"Uploaded and stored {len(all_chunks)} chunks.",
        "skipped_records": skipped
    }

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.97  # default max distance

@app.post("/search")
def search_incidents(req: SearchRequest):
    logger.info(f"Search request: {req.query}, top_k: {req.top_k}, threshold: {req.threshold}")
    # 1. Embed the query
    query_emb = embedding_function.embed_query(req.query)

    # 2. Retrieve top_k similar items
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=req.top_k
    )
    logger.info(f"Retrieved {len(results['documents'][0])} results")

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    logger.info(f"Documents: {docs}")
    logger.info(f"Metadatas: {metas}")
    logger.info(f"Distances: {dists}")

    # 3. Filter by distance threshold
    filtered = []
    for doc, meta, dist in zip(docs, metas, dists):
        if dist < req.threshold:
            filtered.append({
                "document": doc,
                "metadata": meta,
                "distance": dist
            })
    logger.info(f"Filtered results: {filtered}")
    # 4. If none pass, return 404
    if not filtered:
        raise HTTPException(status_code=404, detail="No relevant matches found.")

    return {"results": filtered}
