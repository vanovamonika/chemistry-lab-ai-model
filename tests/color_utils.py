"""
Simple color utilities for comparing hex codes with tolerance.
"""

import re
from typing import Optional


def extract_hex_code(color_string: str) -> Optional[str]:
    """
    Extract hex code from a color description.
    
    Examples:
        "#FF0000, red" -> "#FF0000"
        "#ff0000" -> "#FF0000"
        "no change" -> None
        "none" -> None
    
    Args:
        color_string: Color description string (e.g., "#FF0000, red")
        
    Returns:
        Hex code in uppercase with # prefix, or None if not found
    """
    if not color_string:
        return None
    
    color_string = str(color_string).strip()
    
    # Handle special cases
    if color_string.lower() in ["no change", "none", "unknown"]:
        return None
    
    # Extract hex code pattern (#RRGGBB or #RGB)
    hex_pattern = r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?'
    match = re.search(hex_pattern, color_string)
    
    if match:
        hex_code = match.group(0).upper()
        # Expand 3-digit hex to 6-digit if needed
        if len(hex_code) == 4:  # #RGB format
            hex_code = '#' + ''.join([c * 2 for c in hex_code[1:]])
        return hex_code
    
    return None


def compare_hex_codes(hex1: str, hex2: str, tolerance: int = 50) -> bool:
    """
    Compare two hex codes with tolerance for similar shades.
    
    Uses RGB Euclidean distance: sqrt((R1-R2)^2 + (G1-G2)^2 + (B1-B2)^2)
    
    Args:
        hex1: First hex code (e.g., "#FF0000")
        hex2: Second hex code (e.g., "#FE0000")
        tolerance: Maximum allowed RGB distance (0-441)
                   0 = exact match, 50 = similar shades, 100 = loose match
        
    Returns:
        True if colors are within tolerance, False otherwise
    """
    if not hex1 or not hex2:
        return False
    
    # Convert hex to RGB
    hex1 = hex1.lstrip('#')
    hex2 = hex2.lstrip('#')
    
    r1, g1, b1 = int(hex1[0:2], 16), int(hex1[2:4], 16), int(hex1[4:6], 16)
    r2, g2, b2 = int(hex2[0:2], 16), int(hex2[2:4], 16), int(hex2[4:6], 16)
    
    # Calculate RGB distance
    distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
    
    return distance <= tolerance
