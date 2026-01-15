# Color Comparison Utilities

This module provides utilities for comparing color descriptions with tolerance for similar shades. It's designed to handle color comparisons in visual prediction testing where hex codes don't need to match exactly.

## Features

- **Hex Code Extraction**: Extracts hex codes from color descriptions (e.g., "#FF0000, red" → "#FF0000")
- **Tolerance-Based Comparison**: Compares colors using RGB Euclidean distance with configurable tolerance
- **Color Name Matching**: Also considers color names when comparing descriptions
- **Detailed Reporting**: Provides detailed comparison results for debugging
- **Preset Tolerances**: Pre-defined tolerance levels for common use cases

## Installation

Simply import the color utilities in your test file:

```python
from color_utils import compare_color_descriptions, TOLERANCE_PRESETS
```

## Usage

### Basic Color Comparison

```python
from color_utils import colors_similar

# Compare two colors with default tolerance
predicted = "#FF0000, red"
expected = "#FE0000, red"

if colors_similar(predicted, expected, tolerance=50):
    print("Colors are similar!")
else:
    print("Colors are different")
```

### Detailed Comparison

```python
from color_utils import compare_color_descriptions

predicted = "#FF0000, red"
expected = "#FE0000, red"

match, details = compare_color_descriptions(predicted, expected, tolerance=50)

if match:
    print(f"Colors match! Distance: {details['distance']}")
else:
    print("Colors don't match")
```

### Using Tolerance Presets

```python
from color_utils import colors_similar, TOLERANCE_PRESETS

# Available presets
presets = {
    'exact': 0,           # No tolerance, exact match required
    'strict': 20,         # Very similar shades only
    'normal': 50,         # Good balance (default)
    'loose': 100,         # Allow wider range
    'very_loose': 150,    # Very permissive
}

# Use a preset
if colors_similar(predicted, expected, tolerance=TOLERANCE_PRESETS['strict']):
    print("Colors match strictly!")
```

## Understanding Tolerance

The tolerance parameter represents the maximum RGB distance allowed:

- **Distance = 0**: Identical color
- **Distance ≤ 20**: Very similar shades (strict tolerance)
- **Distance ≤ 50**: Similar shades (normal tolerance) - good for most cases
- **Distance ≤ 100**: Loose matching (allows significant variations)
- **Distance ≤ 441**: Maximum possible distance (black to white)

The RGB distance is calculated using the Euclidean formula:
```
distance = √((R₁-R₂)² + (G₁-G₂)² + (B₁-B₂)²)
```

## Color Format

Colors should be in the format: `#RRGGBB, color_name` or just `#RRGGBB`

Examples:
- `#FF0000, red` (with color name)
- `#00FF00` (hex only)
- `no change` (special case - treated as no color)
- `none` (special case - treated as no color)

## API Reference

### `extract_hex_code(color_string: str) -> Optional[str]`

Extracts hex code from a color description.

**Args:**
- `color_string`: Color description string

**Returns:**
- Hex code in uppercase with # prefix, or None if not found

**Example:**
```python
extract_hex_code("#FF0000, red")  # Returns "#FF0000"
extract_hex_code("no change")     # Returns None
```

### `colors_similar(predicted_color: str, expected_color: str, tolerance: int = 50) -> bool`

Compares two color descriptions for similarity.

**Args:**
- `predicted_color`: Predicted color description
- `expected_color`: Expected color description
- `tolerance`: Maximum allowed RGB distance (0-441)

**Returns:**
- True if colors are similar within tolerance, False otherwise

### `compare_color_descriptions(predicted: str, expected: str, tolerance: int = 50) -> Tuple[bool, dict]`

Compares two color descriptions and returns detailed results.

**Args:**
- `predicted`: Predicted color description
- `expected`: Expected color description
- `tolerance`: Maximum allowed RGB distance

**Returns:**
- Tuple of (match: bool, details: dict)

**Details dict contains:**
- `hex_match`: Whether hex codes are similar
- `name_match`: Whether color names match
- `predicted_hex`: Extracted hex code from predicted
- `expected_hex`: Extracted hex code from expected
- `predicted_name`: Extracted color name from predicted
- `expected_name`: Extracted color name from expected
- `distance`: RGB distance between colors

### `hex_to_rgb(hex_code: str) -> Tuple[int, int, int]`

Converts hex color code to RGB tuple.

**Example:**
```python
hex_to_rgb("#FF0000")  # Returns (255, 0, 0)
```

### `color_distance(hex1: str, hex2: str) -> float`

Calculates RGB Euclidean distance between two colors.

**Example:**
```python
distance = color_distance("#FF0000", "#FE0000")  # Returns ~1.0
```

## Integration with Test Suite

The `api_test.py` file has been updated to use color comparison with tolerance:

```python
from color_utils import compare_color_descriptions, TOLERANCE_PRESETS

# Configure global tolerance
COLOR_TOLERANCE = TOLERANCE_PRESETS['normal']

# In test function
color_match, color_details = compare_color_descriptions(
    predicted_color,
    expected_color,
    tolerance=COLOR_TOLERANCE
)
```

You can adjust the global `COLOR_TOLERANCE` in `api_test.py` to change the strictness of color matching across all tests.

## Examples

Run the example file to see all features in action:

```bash
python tests/color_utils_example.py
```

This will demonstrate:
1. Hex code extraction
2. Color comparison with different tolerances
3. Detailed comparison results
4. Batch testing

## Troubleshooting

**No hex code found in color description:**
- Make sure the hex code follows the format `#RRGGBB` (uppercase or lowercase)
- Example: `#FF0000` not `#ff0000` (though both work)

**Colors don't match with expected tolerance:**
- Check the distance value in the details
- Try increasing the tolerance value
- Example: Use `TOLERANCE_PRESETS['loose']` instead of `'strict'`

**Color names not being matched:**
- Extract the color name correctly
- Use `get_color_name_from_description()` to debug
- Both color names must match exactly

## Testing Color Utils

```bash
# Run the examples
python tests/color_utils_example.py

# Run the API tests with color comparison
python tests/api_test.py
```
