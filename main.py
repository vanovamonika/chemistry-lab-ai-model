#!/usr/bin/env python3
import argparse
import reaction_predictor

# def get_reaction(reaction_type: str, format: str, reactants: str, reagents: str = "", conditions: str = "", temperature: float = 20.0) -> str:
#     reactant_names = reactants
#     reagent_names = reagents
#     if reaction_type == 'inorganic':
#         print("Using inorganic reaction prediction settings.")
#         # You can set specific settings for inorganic reactions here
#         result = query_data.generate_reaction_products(reactants=reactants, reagents=reagents, 
#                         reaction_conditions=conditions, temperature=temperature)
#         print("Generated reaction products:\n", result)
#         return result[0]
         
#     else: # organic or other types
#         print("Using organic reaction prediction settings.")
#         if format == 'names':
#             reactants = smiles_converter.get_smile_reaction_formula_from_names(reactants)
#             if reagents:
#                 reagents = smiles_converter.get_smile_reaction_formula_from_names(reagents)
#             print(f"Converted reactants {reactants} to smiles {reactants}")
#             print(f"Converted reagents {reactants} to smiles {reagents}")

#         products = molecular_transformer.predict_reaction_products(reactants=reactants, reagents=reagents)
#         print("products: " + products)
#         products_names = smiles_converter.get_name_reaction_formula_from_smiles(products)
#         print(products_names)
#         return reactant_names + " + " + reagent_names + " -> " + products_names

def main():
    parser = argparse.ArgumentParser(
        description="A chemical reaction predictor",
        epilog="Example: python reaction_predictor.py --reactants 'CCO.C(=O)O' --model sagawa/ReactionTransformer"
    )
    
    # Required arguments
    parser.add_argument('--reactants', 
                       required=True,
                       help='SMILES string of reactants')
    
    parser.add_argument('--reagents', 
                       default='',
                       help='SMILES string of reagents')
    
    
    parser.add_argument('--temperature', '-t',
                       type=float,
                       default=20.0,
                       help='Temperature of the reaction in Celsius')
    
    parser.add_argument('--conditions', '-c',
                       type=str,
                       default='',
                       help='Chemical reaction conditions description')
    
    parser.add_argument('--type',
                       type=str,
                       default='inorganic',
                       help='Type of chemical reaction (e.g., organic, inorganic)')
        
    # Choices
    parser.add_argument('--format',
                       choices=['smiles', 'names'],
                       default='smiles',
                       help='Output format')
    
    # Multiple values
    # parser.add_argument('--reagents', nargs='+',
    #                    help='List of reagents')
    
    args = parser.parse_args()
    reactants = args.reactants
    reagents = args.reagents
    predictor = reaction_predictor.ReactionPredictor()
    reaction = predictor.predict_reaction(args.type, args.format, reactants, reagents, args.conditions, args.temperature)
    # appearance_predictor = visual_prediction.AppearancePredictor()
    visuals = predictor.predict_visuals(
        type='reaction',
        reaction=reaction,
        conditions=args.conditions)
    print("Predicted visuals:\n", visuals)

if __name__ == "__main__":
    main()