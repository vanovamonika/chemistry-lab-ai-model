import os
import requests
import json

base_url = "http://localhost:8000"

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
    test_results = {"must_contain": {"correct": 0, "wrong": 0}, 
                    "must_not_contain": {"correct": 0, "wrong": 0},
                    "total_tests": len(test_data)}

    for test_case in test_data:
        
        reactants = test_case["reactants"]
        conditions = test_case["conditions"]
        temperature = test_case["temperature"]
        must_contain = test_case["expected"]["must_contain"]
        must_not_contain = test_case["expected"]["must_not_contain"]

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
        print("Predicted products:", predicted_products)
        try:
            assert all(prod in predicted_products for prod in must_contain), f"Expected all of {must_contain}, but got {predicted_products}"
            test_results["must_contain"]["correct"] += 1
        except AssertionError as e:
            print(e)
            test_results["must_contain"]["wrong"] += 1

        try:
            assert all(prod not in predicted_products for prod in must_not_contain), f"Did not expect any of {must_not_contain}, but got {predicted_products}"
            test_results["must_not_contain"]["correct"] += 1
        except AssertionError as e:
            print(e)
            test_results["must_not_contain"]["wrong"] += 1
    print("Test Results:")
    print(test_results)

if __name__ == "__main__":
    predict_products_test("data/test_data.json")
