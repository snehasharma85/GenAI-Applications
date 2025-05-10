# agents/filter_tool.py

from typing import List, Dict
from utils.input_parser import parse_tool_input
import json
from langchain.tools import Tool

def apply_filters(products: List[Dict], filters: Dict) -> List[Dict]:
    print("filters---", filters)
    print("product---", products)
    def match(product):
        if "max_price" in filters and product.get("price", 0) > filters["max_price"]:
            return False
        if "min_price" in filters and product.get("price", 0) < filters["min_price"]:
            return False
        if "min_rating" in filters and filters.get("min_rating") is not None and product.get("rating", 0) < filters["min_rating"]:
            return False
        if "brand" in filters:
            for brand in filters["brand"]:
                if brand.lower() not in product.get("brand", "").lower():
                    return False
        if "features" in filters:
            product_features = product.get("features", [])
            if not isinstance(product_features, list):
                product_features = [f.strip() for f in product_features.split(",")]  # safe fallback
            product_features_lower = [pf.lower() for pf in product_features]
            if not all(f.lower() in product_features_lower for f in filters["features"]):
                return False
    return True

    return [p for p in products if match(p)]


def filtering_tool(input_data) -> str:
    data = parse_tool_input(input_data)
    if isinstance(data, str):  # error case
        return data

    products = data.get("products", [])
    filters = data.get("filters", {})

    if not isinstance(products, list) or not isinstance(filters, dict):
        return "Invalid input: 'products' must be a list and 'filters' must be a dictionary."

    print(f"Applying filters: {json.dumps(filters, indent=2)}")
    print(f"Number of products received: {len(products)}")

    filtered = apply_filters(products, filters)
    #return json.dumps(filtered)
    return json.dumps({"products": filtered}) 


filter_tool = Tool(
    name="FilterTool",
    func=filtering_tool,
    description="Filters products based on extracted filters. Input must include 'products' and 'filters'."
)
