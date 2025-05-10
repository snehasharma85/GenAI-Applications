from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import json
import os
import shutil

# === Step 1: Load dummy data ===
# Get the path to the JSON file relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "../../data/dummy_products.json")

with open(json_path, "r") as f:
    products = json.load(f)

# === Step 2: Prepare documents for Chroma ===
docs = []
for product in products:
    content = (
        f"{product['title']} by {product['brand']} with features "
        f"{', '.join(product['features'])}, priced at ${product['price']}, "
        f"rated {product['rating']} stars with {product['num_reviews']} reviews."
    )
    metadata = {
        "title": product["title"],
        "brand": product["brand"],
        "price": product["price"],
        "rating": product["rating"],
        #"features": ", ".join(product["features"]),
        "features": product["features"],  # Keep it as a list
        "url": product["url"],
        "source": product["source"]
    }
    docs.append(Document(page_content=content, metadata=metadata))
    print(type(metadata["features"]), metadata["features"])

# === Step 3: Initialize embedding model ===
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# === Step 4: Setup Chroma vector store ===

chroma_dir = "../../db/chroma_product_store"
if os.path.exists(chroma_dir):
    shutil.rmtree(chroma_dir)  # Optional: clears previous state

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embedding_model,
    persist_directory=chroma_dir
)

# Persist Chroma DB to disk
vectorstore.persist()
print(docs)