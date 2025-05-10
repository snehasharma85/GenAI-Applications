# agents/semantic_search_tool.py

from typing import Union
import json
from langchain.tools import Tool
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from utils.input_parser import parse_tool_input

# Load embedding model
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load vector store
vectorstore = Chroma(
    persist_directory="../../db/chroma_product_store",
    embedding_function=embedding_model
)

# Toggle this to False in prod
DEBUG = True

def semantic_search(query_input: str) -> str:
    if DEBUG:
        print("\n🔍 Semantic Search Tool Input:\n", query_input)

    data = parse_tool_input(query_input)
    if isinstance(data, str):
        return data

    query = data.get("query", "")
    if not query:
        return json.dumps({"error": "No query found in input."})

    # Load store metadata once
    store_data = vectorstore.get()
    if(store_data is not None):
        print("\n store_data in chroma db ---", store_data)

    if DEBUG:
        print(f"Number of documents in vector store: {len(store_data['documents'])}")
        print("\n🔍 Metadata of Documents in Vector Store:\n")
        for metadata in store_data["metadatas"]:
            print(metadata)

    # Perform search
    print("query before semantic serach--", query)
    results = vectorstore.similarity_search(query, k=10)
    matches = [r.metadata for r in results]
    
    if DEBUG:
        print("\n🔍 Semantic Search results:\n", results)
        print("\n🔍 Semantic Search Tool Output:\n", matches)

    #return json.dumps(matches)
    return json.dumps({"products": matches}) 

# LangChain Tool wrapper
search_tool = Tool(
    name="ProductSearchTool",
    func=semantic_search,
    description="Searches for products semantically. Input should be a JSON with 'query'."
)

# Example usage for CLI
if __name__ == "__main__":
    user_query = json.dumps({
        "query": "Dell gaming laptop with RTX 4060 equivalent GPU and high refresh rate display"
    })
    print("\n🔗 Running semantic search...\n")
    result = semantic_search(user_query)
    print("\n💬 Search Results:\n", result)
