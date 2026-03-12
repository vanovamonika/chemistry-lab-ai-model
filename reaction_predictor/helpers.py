import json
import re
from typing import Any, Dict, List

def get_formatted_prompt(filename: str, **kwargs):
    try:
        with open(filename, 'r') as f:
            prompt_content = f.read()
        print("✅ Loaded prediction prompt from file")
    except Exception as e:
        print(f"❌ Failed to load compound visual prediction prompt: {e}")
        prompt_content = ""   
    # Step 3: Get base prompt and enhance
    formatted_prompt = prompt_content
    for key, value in kwargs.items():
        placeholder = "{" + key + "}"
        formatted_prompt = formatted_prompt.replace(placeholder, str(value))
    
    return formatted_prompt


def extract_products(text: str) -> List[str]:
        """Extract clean product formulas from reaction equation"""
        try:
            # Split by reaction arrow
            parts = re.split(r'->|→|=>|⇌', text)
            if len(parts) < 2:
                return []
            
            products_part = parts[1].strip()
            
            if "No Reaction" in products_part:
                return ["No Reaction"]
            
            # Split by + and clean each product
            products = []
            for prod in products_part.split(" + "):
                prod = prod.strip()
                # Remove state symbols
                prod = re.sub(r'\([a-z]+\)$', '', prod)
                # Remove coefficients
                prod = re.sub(r'^\d+', '', prod)
                if prod:
                    products.append(prod)
            
            return products
            
        except Exception as e:
            print(f"Error extracting products: {e}")
            return []

def parse_solubility(soluble: Any) -> bool:
    """Parse solubility value to boolean"""
    if soluble is None:
        return False
    if isinstance(soluble, bool):
        return soluble
    if isinstance(soluble, str):
        return soluble.lower() in ['true', 'yes', 'soluble', '1']
    return bool(soluble)

def extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON object from LLM response and parse it safely."""
        try:
            if text is None:
                return {}

            # Remove markdown code blocks if present
            if '```json' in text:
                text = text.split('```json', 1)[1].split('```', 1)[0]
            elif '```' in text:
                text = text.split('```', 1)[1].split('```', 1)[0]

            text = text.strip()
            if not text:
                return {}

            # If response contains additional prose, extract first JSON object block
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                text = text[start:end + 1]

            json_str = _clean_json_string(text)
            if not json_str:
                return {}

            parsed = json.loads(json_str)
            return parsed if isinstance(parsed, dict) else {}

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error extracting JSON: {e}")
            return {}

def _clean_json_string(json_str: str) -> str:
    """Clean up JSON string to handle common formatting issues"""
    if not json_str:
        return ""

    # Remove JS-style line comments without destroying valid content
    json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
    
    # Replace single quotes with double quotes
    json_str = json_str.replace("'", '"')
    
    # Remove trailing commas
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Add quotes around unquoted keys
    json_str = re.sub(r'([{,\s])([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
    
    return json_str.strip()