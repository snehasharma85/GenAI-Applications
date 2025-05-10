# utils/input_parser.py

import json
from typing import Union, Dict, Any

def parse_tool_input(input_data: Union[str, Dict]) -> Union[Dict[str, Any], str]:
    print("input data recieved--", input_data)
    if isinstance(input_data, dict):
        return input_data
    elif isinstance(input_data, str):
        try:
            data = json.loads(input_data)
            if not isinstance(data, dict):
                return "Parsed JSON is not a dictionary."
            return data
        except json.JSONDecodeError:
            return "Invalid JSON input string."
    else:
        return "Unsupported input format (must be str or dict)."
