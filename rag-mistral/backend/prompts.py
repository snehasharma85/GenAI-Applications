# prompts.py

from langchain.prompts import PromptTemplate

# Define your system prompt template with web search fallback
SYSTEM_PROMPT = """
You are a helpful, professional banking assistant.
Use ONLY the following context to answer the question.
If the answer is not in the context, you can search the web and include relevant information.

Context:
{context}

Question:
{question}

Answer:
"""
