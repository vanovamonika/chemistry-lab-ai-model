import os
import requests
import json
from color_utils import extract_hex_code, compare_hex_codes

base_url = "http://localhost:8000"
COLOR_TOLERANCE = 50  # Adjust tolerance: 0=exact, 20=strict, 50=normal, 100=loose
LOOSE_TOLERANCE = 100  # For looser color comparisons

def load_test_data(filepath):
        # Load or define test data for organic reactions
        # If the given filepath doesn't exist, try relative to this tests directory
        if not os.path.isabs(filepath) and not os.path.exists(filepath):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(base_dir, filepath)
            if os.path.exists(alt_path):
                filepath = alt_path

        with open(filepath, 'r') as f:
            data = json.load(f)
        return data

def predict_products_test(filepath):
    test_data = load_test_data(filepath)
    test_results = {"must_contain": 0, 
                    "must_not_contain": 0,
                    "correct_equations": 0,
                    "total_tests": len(test_data)}

    for test_case in test_data:
        
        reactants = test_case["reactants"]
        conditions = test_case["conditions"]
        temperature = test_case["temperature"]
        must_contain = test_case["expected"]["must_contain"]
        must_not_contain = test_case["expected"]["must_not_contain"]
        expected_equation = test_case["expected"]["equation"]

        print(f"Testing with reactants: {reactants}, conditions: {conditions}, temperature: {temperature}")
        response = requests.post(
            f"{base_url}/predict/products",
                json={
                    "reactants": reactants,
                    "conditions": conditions,
                    "temperature": temperature,
                }
            )
        print(response)
        predicted_products = response.json().get("products", [])
        predicted_equation = response.json().get("equation", "")
        print("Predicted products:", predicted_products)
        if predicted_products:
            try:
                assert all(prod in predicted_products for prod in must_contain), f"Expected all of {must_contain}, but got {predicted_products}"
                test_results["must_contain"] += 1
            except AssertionError as e:
                print(e)
            try:
                assert all(prod not in predicted_products for prod in must_not_contain), f"Did not expect any of {must_not_contain}, but got {predicted_products}"
                test_results["must_not_contain"] += 1
            except AssertionError as e:
                print(e)
        else:
            print("No products predicted.")
        # if predicted_equation:
        #     try:
        #         assert predicted_equation == expected_equation, f"Expected equation {expected_equation}, but got {predicted_equation}"
        #         test_results["correct_equations"] += 1
        #     except AssertionError as e:
        #         print(e)
        # else:
        #     print("No equation predicted.")
            
    print("Test Results:")
    print(test_results)

def query_api_and_get_visual_description(endpoint, payload):
    response = requests.post(
        f"{base_url}{endpoint}",
        json=payload
    )
    print(response)
    if response.status_code == 200:
        data = response.json()
        # print("Response data:", data)
        visual_description = data.get("visual_description", {})
        # if visual_type == "compound":
        #     visual_description = visual_description.get("visual_description", {})
        # print(f"Visual description: {visual_description}")
        return visual_description
    else:
        print(f"✗ HTTP {response.status_code}")
        return None
    
def test_color_state(predicted, expected):
    """
    Compare predicted and expected visual descriptions for color and state.
    
    Args:
        predicted: Predicted visual description dict
        expected: Expected visual description dict
        
    Returns:
        Tuple of (color_match: bool, state_match: bool)
    """
    predicted_color = predicted.get("color", "unknown")
    expected_color = expected.get("color", "unknown")
    
    # Extract hex codes and compare with tolerance
    predicted_hex = extract_hex_code(str(predicted_color))
    expected_hex = extract_hex_code(str(expected_color))
    
    hex_color_match = compare_hex_codes(predicted_hex, expected_hex, tolerance=COLOR_TOLERANCE)
    loose_hex_color_match = compare_hex_codes(predicted_hex, expected_hex, tolerance=LOOSE_TOLERANCE)
    # Compare states
    predicted_state = str(predicted.get("state", "unknown")).lower()
    expected_state = str(expected.get("state", "unknown")).lower()
    state_match = expected_state in predicted_state
    
    # Print comparison results
    print(f"Predicted color: {predicted_color}")
    print(f"Expected color: {expected_color}")
    print(f"  Predicted hex: {predicted_hex}")
    print(f"  Expected hex: {expected_hex}")
    print(f"  Color match: {hex_color_match}")
    print(f"Predicted state: {predicted_state}, Expected state: {expected_state}")
    print(f"State match: {state_match}")
    return hex_color_match, state_match, loose_hex_color_match, 

def predict_compound_visuals_test(filepath):
    """
    Test the compound visuals prediction endpoint
    
    Args:
        filepath: Path to JSON file containing test compounds
                 Expected format: [{"compound": "H2O", "conditions": "room temperature"}, ...]
    """
    test_data = load_test_data(filepath)
    test_results = {
        "color": 0,
        "loose_color": 0,
        "state": 0,
        "total_tests": len(test_data),
    }
    
    for test_case in test_data:
        compound = test_case.get("compound", "")
        conditions = test_case.get("conditions", "standard conditions")
        
        print(f"\nTesting compound: {compound}, conditions: {conditions}")
        
        try:
            visual_description = query_api_and_get_visual_description(
                "/predict/compound_visuals",
                {
                    "compound": compound,
                    "conditions": conditions,
                })

            if visual_description and isinstance(visual_description, dict):
                expected_visual = test_case.get("expected", {}).get("visual_description", {})
                print(f"Expected visual description: {expected_visual}")
                color_match, state_match, loose_color_match = test_color_state(visual_description, expected_visual)
                if color_match:
                    test_results["color"] += 1
                if state_match:
                    test_results["state"] += 1
                if loose_color_match:
                    test_results["loose_color"] += 1
            else:
                print(f"✗ Empty response or invalid format")
        
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\nTest Results:")
    print(test_results)

def predict_reaction_visuals_test(filepath):
    """
    Test the reaction visuals prediction endpoint
    
    Args:
        filepath: Path to JSON file containing test reactions
                 Expected format: [{"reaction": "H2 + O2 -> H2O", "products": "H2O", "reactant_visuals": "...", "conditions": "room temperature"}, ...]
    """
    test_data = load_test_data(filepath)
    test_results = {
        "middle" : {"color": 0, "loose_color": 0, "state": 0},
        "final" : {"color": 0, "loose_color": 0, "state": 0},
        "total_tests": len(test_data),
    }
    
    for test_case in test_data:
        reaction = test_case.get("reaction", "")
        products = test_case.get("products", "")
        reactant_visuals = test_case.get("reactant_visuals", "")
        conditions = test_case.get("conditions", "standard conditions")
        expected_visuals = test_case.get("expected", {}).get("visual_description", {})
        
        print(f"\nTesting reaction: {reaction}, products: {products}, conditions: {conditions}")
        
        try:
            visual_description = query_api_and_get_visual_description(
                "/predict/reaction_visuals",
                {
                    "reaction": reaction,
                    "products": products,
                    "reactant_visuals": reactant_visuals,
                    "conditions": conditions,
                })

            if visual_description and isinstance(visual_description, dict):
                # print(f"Expected visual description: {expected_visuals}")
                # print(f"Predicted visual description: {visual_description}")
                middle_visual = visual_description.get("middle_of_reaction", {})
                expected_middle_visual = expected_visuals.get("middle_of_reaction", {})
                middle_color_match, middle_state_match, middle_loose_color_match = test_color_state(middle_visual, expected_middle_visual)
                if middle_color_match:
                    test_results["middle"]["color"] += 1
                if middle_loose_color_match:
                    test_results["middle"]["loose_color"] += 1
                if middle_state_match:
                    test_results["middle"]["state"] += 1
                
                final_visual = visual_description.get("final_state", {})
                expected_final_visual = expected_visuals.get("final_state", {})
                final_color_match, final_state_match, final_loose_color_match = test_color_state(final_visual, expected_final_visual)
                if final_color_match:
                    test_results["final"]["color"] += 1
                if final_loose_color_match:
                    test_results["final"]["loose_color"] += 1
                if final_state_match:
                    test_results["final"]["state"] += 1
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\nTest Results:")
    print(test_results)


if __name__ == "__main__":
    # predict_products_test("data/products_test_data.json")
    # predict_products_test("data/organic_test_data.json")
    # predict_products_test("data/inorganic_test_data.json")
    predict_compound_visuals_test("data/compound_visuals_test_data.json")
    # predict_reaction_visuals_test("data/reaction_visuals_test_data.json")
