# agents/response_generator.py

import json
from typing import List, Dict, Union
from utils.input_parser import parse_tool_input
from langchain.tools import Tool
from langchain_community.llms import Ollama

# Load Mistral via Ollama
llm = Ollama(model="mistral", temperature=0.0)

# Fallback text formatter
def generate_response(products: List[Dict]) -> str:
    if not products:
        return "No matching products found."
    lines = ["Here are some products you might like:\n"]
    for p in products[:5]:
        lines.append(f"- {p['title']} (${p['price']}, rated {p['rating']}⭐) → {p['url']}")
    print("response gneertaed by text not LLM")
    return "\n".join(lines)

# Main response tool
def response_tool_func(input_data: Union[str, List[Dict]]) -> str:
    # Parse input
    if isinstance(input_data, list):
        products = input_data
        print("products in if block-----", products)
    else:
        parsedInput = parse_tool_input(input_data)
        print("parsedInput-----", parsedInput)
        if isinstance(parsedInput, str):  # error string
            return parsedInput
        products = parsedInput.get("products", [])
        print("products in else block-----", products)

    # Validate
    if not isinstance(products, list) or not products:
        return "Sorry, I couldn't find any products matching your criteria. Please try adjusting your filters."

    # Format product info
    product_context = "\n".join([
        f"Product: {p['title']}, Price: ${p['price']}, Rating: {p['rating']}/5, URL: {p['url']}"
        for p in products[:5]
    ])
    
    llm_prompt = f"""
    Based on the following product information, create a helpful shopping recommendation:

    {product_context}

    Make the response user-friendly and engaging.
    Include product URLs in the response if available.
    """

    # Call LLM safely
    try:
        llm_response = llm.invoke(llm_prompt)
        if not llm_response.strip():        
            raise ValueError("Empty response")
        return llm_response
    except Exception as e:
        print(f"⚠️ LLM error: {e}")
        return generate_response(products)

# LangChain Tool wrapper
response_tool = Tool(
    name="ResponseFormatter",
    func=response_tool_func,
    description="Converts filtered product list (in JSON) into a user-friendly response.",
    return_direct=True
)
