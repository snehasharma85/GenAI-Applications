# agents/intent_extraction_tool.py

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import Ollama
from langchain.tools import Tool
from typing import Dict
import json
import re

# Load LLM
llm = Ollama(model="mistral", temperature=0.0)

# Prompt to extract filters as strict JSON
prompt = PromptTemplate.from_template("""
You are a helpful assistant. Extract shopping intent from the following user query.
Convert it into a JSON object with possible fields: category, brand, min_price, max_price, min_rating, features (list of keywords).

User Query: {query}

Respond with JSON only. Do not include any additional text or explanations.
""")

# Chain setup
intent_chain = LLMChain(llm=llm, prompt=prompt)

# Core function
def extract_intent(query: str) -> str:
    response = intent_chain.run(query)
    print("\n🔍 Intent Extraction Output:\n", response)
    
    # Extract just the JSON if LLM added any fluff
    match = re.search(r'{.*}', response, re.DOTALL)
    if not match:
        return json.dumps({"error": "Could not extract valid JSON"})
    
    try:
        filters = json.loads(match.group(0))
        if not isinstance(filters, dict):
            return json.dumps({"error": "Intent is not a dictionary."})
        return json.dumps(filters)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON format in extracted intent"})

# Tool wrapper
intent_extraction_tool = Tool(
    name="IntentExtractionTool",
    func=extract_intent,
    description="Extracts structured filters (e.g., category, brand, price range) from a shopping query."
)
