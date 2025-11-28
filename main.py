#!/usr/bin/env python3
import argparse
import smiles_converter
import molecular_transformer
import query_data

# import visual_prediction

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
    
    # Optional arguments
    parser.add_argument('--model', '-m',
                       default='sagawa/ReactionTransformer',
                       help='Hugging Face model to use')
    
    parser.add_argument('--temperature', '-t',
                       type=float,
                       default=20.0,
                       help='Sampling temperature')
    
    parser.add_argument('--conditions', '-c',
                       type=str,
                       default='aqueous solution, room temperature',
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

    if args.type == 'inorganic':
        print("Using inorganic reaction prediction settings.")
        # You can set specific settings for inorganic reactions here
        query_data.main(reactants=reactants, reagents=reagents, 
                        reaction_conditions=args.conditions, temperature=args.temperature)
        return

    else: # organic or other types
        print("Using organic reaction prediction settings.")
        if args.format == 'names':
            reactants = smiles_converter.get_smile_reaction_formula_from_names(args.reactants)
            if args.reagents:
                reagents = smiles_converter.get_smile_reaction_formula_from_names(args.reagents)
            print(f"Converted reactants {args.reactants} to smiles {reactants}")
            print(f"Converted reagents {args.reactants} to smiles {reagents}")

        products = molecular_transformer.predict_reaction_products(reactants=reactants, reagents=reagents)
        print("products: " + products)
        products_names = smiles_converter.get_name_reaction_formula_from_smiles(products)
        
        print(products_names)

if __name__ == "__main__":
    main()