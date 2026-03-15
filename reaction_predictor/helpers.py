import json
import re
from typing import Any, Dict, List


NO_REACTION_MARKERS = [
    "no reaction",
    "no reaction occurs",
    "no reaction occurs under the given conditions",
]


def normalize_equation_line(text: str) -> str:
    """Return a best-effort single equation line from raw model output."""
    if not text:
        return ""

    cleaned = text.strip()

    # Remove markdown code fences if present
    if "```" in cleaned:
        cleaned = cleaned.replace("```", "\n")

    # Use only first logical line / statement
    first_line = re.split(r"[\n;]", cleaned, maxsplit=1)[0].strip()
    return first_line


def _contains_url_artifact(value: str) -> bool:
    lowered = value.lower()
    url_markers = ["http://", "https://", "www.", ".html", "#:~:text", "%2c", "/"]
    return any(marker in lowered for marker in url_markers)


def _normalize_product_token(token: str) -> str:
    # Remove leading stoichiometric coefficient
    token = re.sub(r"^\s*\d+\s*", "", token.strip())
    # Remove terminal state marker, e.g. (aq), (s), (l), (g)
    token = re.sub(r"\((aq|s|l|g)\)\s*$", "", token, flags=re.IGNORECASE)
    return token.strip()


def _looks_like_chemical_formula(token: str) -> bool:
    """Heuristic formula validator. Permissive for ions/complexes, strict on non-chemical text."""
    if not token:
        return False
    if len(token) > 40:
        return False
    if _contains_url_artifact(token):
        return False
    if any(ch in token for ch in [":", "=", "?", "#", "&", ","]):
        return False

    # Must contain at least one element-like token
    if not re.search(r"[A-Z][a-z]?", token):
        return False

    # Allowed chemistry characters (plus dot for hydrates, +/- for ions)
    if not re.fullmatch(r"[A-Za-z0-9\(\)\[\]\+\-\.·^]+", token):
        return False

    # Avoid long lowercase words accidentally captured from prose
    if re.search(r"[a-z]{3,}", token):
        return False

    return True


def is_no_reaction_text(value: str) -> bool:
    normalized = (value or "").strip().lower()
    return any(marker in normalized for marker in NO_REACTION_MARKERS)


def validate_reaction_output(equation: str, products: List[str]) -> tuple[bool, str, List[str], str]:
    """
    Validate and clean predicted reaction output.
    Returns: (is_valid, reason, cleaned_products, cleaned_equation)
    """
    cleaned_equation = normalize_equation_line(equation)

    if not cleaned_equation:
        return False, "Empty equation", [], ""

    if _contains_url_artifact(cleaned_equation):
        return False, "Equation contains URL/web artifact", [], cleaned_equation

    if is_no_reaction_text(cleaned_equation):
        return True, "No reaction output accepted", ["No reaction occurs"], cleaned_equation

    if not re.search(r"->|→|=>|⇌", cleaned_equation):
        return False, "Equation missing reaction arrow", [], cleaned_equation

    # Trust equation-derived products over free-form list
    parsed_products = extract_products(cleaned_equation)
    source_products = parsed_products if parsed_products else products

    if not source_products:
        return False, "No products found", [], cleaned_equation

    cleaned_products: List[str] = []
    for product in source_products:
        if is_no_reaction_text(product):
            return True, "No reaction output accepted", ["No reaction occurs"], cleaned_equation

        normalized_product = _normalize_product_token(product)
        if not _looks_like_chemical_formula(normalized_product):
            return False, f"Invalid product token: {product}", [], cleaned_equation
        cleaned_products.append(normalized_product)

    return True, "Valid", cleaned_products, cleaned_equation

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
            # Retry once for templated outputs like {{ ... }}
            try:
                normalized = _normalize_wrapped_json_object(_clean_json_string(text))
                if normalized:
                    parsed = json.loads(normalized)
                    return parsed if isinstance(parsed, dict) else {}
            except Exception:
                pass

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

    # Normalize templated wrappers like {{ ... }} -> { ... }
    json_str = _normalize_wrapped_json_object(json_str)
    
    return json_str.strip()


def _normalize_wrapped_json_object(value: str) -> str:
    """Convert templated JSON wrappers like '{{ ... }}' into valid JSON '{ ... }'."""
    if not value:
        return ""

    normalized = value.strip()

    # Some LLM prompts/template engines escape braces by doubling them.
    # Keep unwrapping while the full payload is wrapped by double braces.
    while normalized.startswith("{{") and normalized.endswith("}}"):
        normalized = "{" + normalized[2:-2].strip() + "}"

    return normalized

def color_name_to_hex(color_name: str) -> str:
    """Convert color names to hex codes with advanced pattern matching."""
    color_map = {
        "red": "#FF0000", "blue": "#0000FF", "green": "#008000",
        "yellow": "#FFFF00", "orange": "#FFA500", "purple": "#800080",
        "pink": "#FFC0CB", "brown": "#A52A2A", "black": "#000000",
        "white": "#FFFFFF", "gray": "#808080", "grey": "#808080",
        "cyan": "#00FFFF", "magenta": "#FF00FF", "violet": "#EE82EE"
    }
    
    color_lower = color_name.lower()
    
    # Pattern 1: Direct match
    if color_lower in color_map:
        return color_map[color_lower]
    
    # Pattern 2: Contains color word
    for color, hex_code in color_map.items():
        if color in color_lower:
            # Check for modifiers
            if any(word in color_lower for word in ["light", "pale", "soft"]):
                return lighten_color(hex_code)
            elif any(word in color_lower for word in ["dark", "deep"]):
                return darken_color(hex_code)
            return hex_code
    
    # Pattern 3: Hexadecimal-like strings
    hex_pattern = r'#?[0-9A-Fa-f]{6}'
    matches = re.findall(hex_pattern, color_name)
    if matches:
        hex_match = matches[0]
        if not hex_match.startswith('#'):
            hex_match = '#' + hex_match
        return hex_match
    
    # Pattern 4: RGB values
    rgb_pattern = r'(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})'
    matches = re.search(rgb_pattern, color_name)
    if matches:
        r, g, b = map(int, matches.groups())
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # Pattern 5: Descriptive colors
    descriptive_map = {
        r'colorless|clear|transparent': "#FFFFFF",
        r'golden?': "#FFD700",
        r'silvery?': "#C0C0C0",
        r'copper': "#B87333",
        r'brass': "#B5A642",
        r'bronze': "#CD7F32",
        r'rose': "#FF007F",
        r'lavender': "#E6E6FA",
        r'peach': "#FFE5B4",
        r'mint': "#98FB98",
        r'coral': "#FF7F50",
        r'amber': "#FFBF00",
        r'ruby': "#E0115F",
        r'emerald': "#50C878",
        r'sapphire': "#0F52BA"
    }
    
    for pattern, hex_code in descriptive_map.items():
        if re.search(pattern, color_lower):
            return hex_code
    
    # Default
    return "#CCCCCC"

def lighten_color(hex_color: str, factor: float = 0.3) -> str:
    """Lighten a hex color by mixing with white."""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return rgb_to_hex(r, g, b)

def darken_color(hex_color: str, factor: float = 0.4) -> str:
    """Darken a hex color."""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return rgb_to_hex(r, g, b)

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"