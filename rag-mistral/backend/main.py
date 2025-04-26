from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM
from prompts import SYSTEM_PROMPT
import requests
import os
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize folders
os.makedirs("docs", exist_ok=True)
os.makedirs("db", exist_ok=True)

# Initialize core components
logger.info("Initializing embeddings and vector store...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if os.path.exists("db/chroma.sqlite3"):
    logger.info("Loading existing Chroma vectorstore...")
    vectordb = Chroma(persist_directory="db", embedding_function=embeddings)
else:
    logger.info("No existing Chroma DB, starting fresh...")
    vectordb = Chroma(persist_directory="db", embedding_function=embeddings)

retriever = vectordb.as_retriever(
    search_type="mmr",    # maximal marginal relevance
    search_kwargs={"k": 8}   # fetch more documents
)

llm = OllamaLLM(model="mistral")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

# Configuration for web search (SerpAPI in this example)
SERP_API_KEY = "8cbc43cef244483ba4d75545f8033e0d80f813ce29b8a823c23c5352b7bd6da9"
SEARCH_ENGINE_URL = "https://serpapi.com/search"

# Helper
def process_and_add_documents(documents, filename):
    logger.info("Splitting and embedding documents...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # Attach filename into metadata
    for chunk in chunks:
        chunk.metadata["source"] = filename

    logger.info(f"Adding {len(chunks)} chunks from {filename} to vectorstore...")
    vectordb.add_documents(chunks)

    logger.info("Persisting database...")
    vectordb.persist()
    logger.info("Done.")

# Helper function to perform web search using SerpAPI
def search_web(query: str):
    """
    Search the web using SerpAPI and return the most relevant results.
    """
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google"  # You can change to other engines like "bing"
    }

    response = requests.get(SEARCH_ENGINE_URL, params=params)
    search_results = []

    if response.status_code == 200:
        data = response.json()
        for result in data.get("organic_results", []):
            search_results.append(result.get("snippet", "No snippet available"))
    return search_results        


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    logger.info(f"Received upload: {file.filename}")
    temp_path = f"docs/{file.filename}"

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    loader = PyPDFLoader(temp_path)
    documents = loader.load()

    process_and_add_documents(documents, filename=file.filename)

    return {"message": f"Uploaded and processed {file.filename}"}

@app.post("/ask")
async def ask_question(query: str = Form(...)):
    if qa is None:
        logger.error("QA system not ready!")
        return {"error": "QA system not ready. Please upload documents first."}

    logger.info(f"Query received: {query}")

    # Step 1: semantic search *with* scores
    raw_results = vectordb.similarity_search_with_score(query, k=8)
    # filter by threshold
    THRESHOLD = 0.9
    relevant_docs = [doc for doc, score in raw_results if score < THRESHOLD]

    # debug log
    for doc, score in raw_results:
        logger.info(f"{doc.metadata['source']} (score={score:.3f}) → {doc.page_content[:80]}")

    used_web_search = False 
    
    # Step 2: build context or fallback
    if relevant_docs:
        context = "\n\n".join(d.page_content for d in relevant_docs)
    else:
        logger.info("No relevant PDF context—searching the web")
        search_results = search_web(query)
        context = "\n\n".join(search_results)
        used_web_search = True


    # Step 3: Format the prompt with the combined context (from PDFs + Web search if needed)
    prompt = SYSTEM_PROMPT.format(context=context, question=query)

    # Step 4: Generate a response using the LLM (e.g., Ollama model)
    response = llm.invoke(prompt)
    sources = [doc.metadata.get("source", "Unknown") for doc in relevant_docs]
    if used_web_search:
        sources.append("Web")
    # Step 5: Return the result with sources
    return {
        "answer": response,
        "sources": sources
    }

@app.delete("/clear")
async def clear_data():
    logger.info("Clearing all documents and vector database...")
    
    # Remove folders safely
    if os.path.exists("docs"):
        shutil.rmtree("docs")
    if os.path.exists("db"):
        shutil.rmtree("db")

    # Recreate empty folders
    os.makedirs("docs", exist_ok=True)
    os.makedirs("db", exist_ok=True)

    # Reinitialize vector store
    global vectordb, retriever, qa

    # 🛠 Rebuild Chroma correctly
    vectordb = Chroma(persist_directory="db", embedding_function=embeddings)
    retriever = vectordb.as_retriever()
    qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

    logger.info("Reset complete, system ready.")
    return JSONResponse(content={"message": "All documents and database cleared successfully."})

@app.get("/list_documents") # to check what docs are saved into the db
async def list_documents():
    results = vectordb.get()
    docs = []

    for doc_id, metadata, document in zip(results['ids'], results['metadatas'], results['documents']):
        docs.append({
            "id": doc_id,
            "source": metadata.get('source', 'unknown'),
            "text": document[:100] + "..."  # Show first 100 chars for preview
        })

    return docs