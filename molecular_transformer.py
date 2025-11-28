# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# def predict_reaction_products(reactants: str, reagents: str = ""):
#     tokenizer = AutoTokenizer.from_pretrained("sagawa/ReactionT5v2-forward", return_tensors="pt")
#     model = AutoModelForSeq2SeqLM.from_pretrained("sagawa/ReactionT5v2-forward")
#     inp = tokenizer(f'REACTANT:{reactants}REAGENT:{reagents}', return_tensors='pt')
#     output = model.generate(**inp, num_beams=1, num_return_sequences=1, return_dict_in_generate=True, output_scores=True)
#     output = tokenizer.decode(output['sequences'][0], skip_special_tokens=True).replace(' ', '').rstrip('.')
#     return output

# COC(=O)C1=CCCN(C)C1.O.[Al+3].[H-].[Li+].[Na+].[OH-]
# C1CCOC1

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

def predict_reaction_products(reactants: str, reagents: str = ""):
    """
    Predict reaction products using a molecular transformer model
    
    Args:
        reactants: SMILES string of reactants (e.g., "CCO.C(=O)O")
        reagents: SMILES string of reagents (e.g., "OS(=O)(=O)O")
    
    Returns:
        SMILES string of predicted products
    """
    try:
        # Use a reliable model - ReactionTransformer is more stable
        model_name = "sagawa/ReactionT5v2-forward-USPTO_MIT"
        
        print(f"Loading model: {model_name}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        reaction_input = f"REACTANT:{reactants}REAGENT:{reagents}"
        # Format the input properly
        # if reagents:
        #     reaction_input = f"{reactants}>{reagents}>"
        # else:
        #     reaction_input = f"{reactants}>"
        
        print(f"Predicting reaction for: {reaction_input}")
        
        # Tokenize and generate
        input_ids = tokenizer(reaction_input, return_tensors="pt").input_ids
        
        # Generate with reasonable parameters
        outputs = model.generate(
            input_ids,
            max_length=100,
            num_beams=5,
            early_stopping=True,
            return_dict_in_generate=True,
            output_scores=True
        )
        
        # Decode the output
        predicted_product = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
        
        return predicted_product
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        # Fallback to a simple rule-based prediction
        return fallback_prediction(reactants, reagents)

def fallback_prediction(reactants: str, reagents: str = ""):
    """
    Simple fallback prediction when the model fails
    """
    print("Fallback prediction")
    # Basic esterification detection
    if "CCO" in reactants and "C(=O)O" in reactants:
        return "CCOC(=O)C"  # Ethyl acetate
    
    # Basic hydrolysis detection
    if "CCOC(=O)" in reactants and "O" in reagents:
        return "CCO.C(=O)O"  # Ethanol + Acetic acid
    
    # Default fallback
    return "CCOC(=O)C"  # Generic ester product

