import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings  
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM  

# Step 1: Load the PDF
#loader = PyPDFLoader("docs/current.pdf")
#documents = loader.load()

# Folder containing PDFs
pdf_folder = "docs"

# Load and combine all PDF documents
documents = []
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(pdf_folder, filename))
        documents.extend(loader.load())

# Step 2: Split into manageable chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# Step 3: Embed & store in Chroma DB
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  
vectordb = Chroma.from_documents(chunks, embedding=embedding_model, persist_directory="db")
retriever = vectordb.as_retriever()

# Step 4: Connect to local Mistral using the modern Ollama wrapper
llm = OllamaLLM(model="mistral")

# Step 5: Create Retrieval-Augmented QA Chain
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

# Step 6: Ask a question!
query = "What are the key takeaways from this document and which are pdfs are you referring to. Can you also list down the info at document level?"
result = qa.invoke({"query": query})

# Print the result
print("The summarised answer is ----------", result["result"])
