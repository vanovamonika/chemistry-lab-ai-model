#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import reaction_predictor.reaction_predictor_class as rp
import reaction_predictor.smiles_converter as sc
class ReactionPredictorTest():
    def __init__(self):
        self.predictor = rp.ReactionPredictor()

    def load_test_data(self, filepath):
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

    def predict_reactions(self):
        test_data = self.load_test_data("data/test_data.json")
        # print(test_data)
        for test_case in test_data:
            
            reactants = test_case["reactants"]
            conditions = test_case["conditions"]
            temperature = test_case["temperature"]
            expected_products = test_case["expected"]["must_contain"]
            # expected_products = test_case["expected"]["products"]

            print(f"Testing with reactants: {reactants}, conditions: {conditions}, temperature: {temperature}")
            predicted_reaction = self.predictor.predict_organic_reaction(
                reactants=reactants,
                reaction_conditions=conditions,
                temperature=temperature
            )
            print(f"Predicted reaction: {predicted_reaction}")
            parts = predicted_reaction.split("->")
            if len(parts) != 2:
                raise ValueError(f"Invalid reaction format: {predicted_reaction}")
            predicted_products = parts[1].strip().split(" + ")
            print(f"Predicted product: {predicted_products}")
            predicted_names = sc.get_name_reaction_formula_from_smiles(predicted_products).split(" + ")
            print(f"Predicted product names: {predicted_names}")
            expected_names = sc.get_name_reaction_formula_from_smiles(".".join(expected_products)).split(" + ")
            print(f"Expected product names: {expected_names}")
            assert all(prod in predicted_names for prod in expected_names), f"Expected all of {expected_products}, but got {predicted_products}"

if __name__ == "__main__":
    tester = ReactionPredictorTest()
    tester.predict_reactions()
