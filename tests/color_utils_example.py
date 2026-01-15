"""
Example usage of color utilities for color comparison.
"""

from color_utils import (
    extract_hex_code,
    compare_color_descriptions,
    colors_similar,
    TOLERANCE_PRESETS,
)

# Example 1: Extract hex codes
print("=" * 60)
print("Example 1: Extracting hex codes from color descriptions")
print("=" * 60)

examples = [
    "#FF0000, red",
    "#00FF00, green",
    "#0000FF, blue",
    "no change",
    "none",
    "#fff, white",
]

for example in examples:
    hex_code = extract_hex_code(example)
    print(f"'{example}' -> {hex_code}")

# Example 2: Compare colors with different tolerances
print("\n" + "=" * 60)
print("Example 2: Comparing colors with different tolerances")
print("=" * 60)

test_cases = [
    ("#FF0000, red", "#FF0000, red"),          # Exact match
    ("#FF0000, red", "#FE0000, red"),          # Very similar red
    ("#FF0000, red", "#CC0000, red"),          # Slightly different red
    ("#FF0000, red", "#00FF00, green"),        # Different color
    ("no change", "no change"),                 # Both "no change"
]

for predicted, expected in test_cases:
    print(f"\nPredicted: {predicted}")
    print(f"Expected:  {expected}")
    
    for preset_name, tolerance in TOLERANCE_PRESETS.items():
        match = colors_similar(predicted, expected, tolerance)
        status = "✓ Match" if match else "✗ No match"
        print(f"  [{preset_name:10}] tolerance={tolerance:3} -> {status}")

# Example 3: Detailed comparison
print("\n" + "=" * 60)
print("Example 3: Detailed color comparison")
print("=" * 60)

predicted = "#FF0005, red"
expected = "#FF0000, red"

match, details = compare_color_descriptions(predicted, expected, tolerance=50)

print(f"Predicted: {predicted}")
print(f"Expected:  {expected}")
print(f"\nComparison Result: {match}")
print(f"Details:")
for key, value in details.items():
    print(f"  {key:20}: {value}")

# Example 4: Multiple test cases
print("\n" + "=" * 60)
print("Example 4: Batch testing")
print("=" * 60)

test_data = [
    {
        "predicted_color": "#FF0000, red",
        "expected_color": "#FE0000, red",
        "tolerance": "normal",
    },
    {
        "predicted_color": "#0000FF, blue",
        "expected_color": "#0000FF, blue",
        "tolerance": "strict",
    },
    {
        "predicted_color": "#FFA500, orange",
        "expected_color": "#FFB500, orange",
        "tolerance": "loose",
    },
]

for i, test in enumerate(test_data, 1):
    tolerance_value = TOLERANCE_PRESETS[test["tolerance"]]
    match, details = compare_color_descriptions(
        test["predicted_color"],
        test["expected_color"],
        tolerance=tolerance_value
    )
    
    print(f"\nTest {i}:")
    print(f"  Predicted: {test['predicted_color']}")
    print(f"  Expected:  {test['expected_color']}")
    print(f"  Tolerance: {test['tolerance']} ({tolerance_value})")
    print(f"  Result:    {'✓ PASS' if match else '✗ FAIL'}")
    print(f"  Distance:  {details['distance']}")
