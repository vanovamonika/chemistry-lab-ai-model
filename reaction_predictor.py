import argparse
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM  # Changed this
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import smiles_converter

CHROMA_PATH = "chroma"
PROMPT_FILE_PATH = "prompts/only_products_prompt.md"
ANALYZE_REACTANTS_PROMPT_PATH = "prompts/analyze_reactants_prompt.md"

class ReactionPredictor:
    def __init__(self):
        self.model = OllamaLLM(model="phi3:mini")

    def load_prompt_template(self, file_path):
        
        """Load prompt template from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                prompt_content = file.read()
            return prompt_content
        except FileNotFoundError:
            print(f"Error: Prompt file not found at {file_path}")
            return None
        except Exception as e:
            print(f"Error loading prompt file: {e}")
            return None

    def predict_inorganic_reaction(self, reactants, reagents="", reaction_conditions="", temperature=20.0):
        analyze_reactants_prompt_content = self.load_prompt_template(ANALYZE_REACTANTS_PROMPT_PATH)
        analyze_reactants_prompt = ChatPromptTemplate.from_template(analyze_reactants_prompt_content)
        reactant_analysis_prompt = analyze_reactants_prompt.format(reactants=reactants, reagents=reagents)
        reactants_analysis = self.model.invoke(reactant_analysis_prompt)
        print("Reactants analysis:\n", reactants_analysis)

        # Load the prompt template
        prompt_template_content = self.load_prompt_template(PROMPT_FILE_PATH)
        if not prompt_template_content:
            print("Using fallback prompt...")
            # Fallback to a simple prompt if file loading fails
            prompt_template_content = """
            Context: {context}
            Question: {question}
            
            Please analyze this chemical reaction and predict the products.
            """

        # Prepare the DB with the same embeddings used for creation
        embedding_function = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

        # Search the DB.
        results = db.similarity_search_with_relevance_scores(reactants_analysis, k=3)
        if len(results) == 0:
            print(f"Unable to find matching results.")
            return

        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt_template = ChatPromptTemplate.from_template(prompt_template_content)
        prompt = prompt_template.format(reactants=reactants, reagents=reagents,
                                    reaction_conditions=reaction_conditions, 
                                    temperature=temperature, context=context_text, reactants_analysis=reactants_analysis)
        print("Context used:\n", context_text)
        print("\n" + "="*50 + "\n")
        print("Generating response...")
        response_text = self.model.invoke(prompt)

        # sources = [doc.metadata.get("source", None) for doc, _score in results]
        # formatted_response = f"Response: {response_text}\nSources: {sources}"
        # print(formatted_response)
        result = response_text.split("\n\n")
        # print("Generated reaction products:\n", result)
        return result[0]
    
    def predict_organic_reaction(self, reactants, reagents="", reaction_conditions="", temperature=20.0):
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
    
    def predict_visuals(self, type, reaction, conditions="standard conditions"):
        prompt_files = {
            "compound": "prompts/compound_visual_prediction_prompt.md",
            "reaction": "prompts/reaction_visual_prediction_prompt.md"
        }
        file_path = prompt_files.get(type)
        prompt = self.load_prompt_template(file_path)
        visuals_prompt = ChatPromptTemplate.from_template(prompt)
        formatted_visuals_prompt = visuals_prompt.format(reaction=reaction, conditions=conditions)
        visuals = self.model.invoke(formatted_visuals_prompt)
        # print(f"visuals:\n{visuals}")
        return self.extract_json(visuals)

    def predict_reaction(self, reaction_type: str, format: str, reactants: str, reagents: str = "", conditions: str = "", temperature: float = 20.0) -> str:
        reactant_names = reactants
        reagent_names = reagents
        if reaction_type == 'inorganic':
            print("Using inorganic reaction prediction settings.")
            # You can set specific settings for inorganic reactions here
            result = self.predict_inorganic_reaction(reactants=reactants, reagents=reagents, 
                            reaction_conditions=conditions, temperature=temperature)
            print("Generated reaction products:\n", result)
            return result
             
        else: # organic or other types
            print("Using organic reaction prediction settings.")
            if format == 'names':
                reactants = smiles_converter.get_smile_reaction_formula_from_names(reactants)
                if reagents:
                    reagents = smiles_converter.get_smile_reaction_formula_from_names(reagents)
                print(f"Converted reactants {reactants} to smiles {reactants}")
                print(f"Converted reagents {reactants} to smiles {reagents}")

            products = self.predict_organic_reaction(reactants=reactants, reagents=reagents)
            print("products: " + products)
            products_names = smiles_converter.get_name_reaction_formula_from_smiles(products)
            print(products_names)
            return reactant_names + " + " + reagent_names + " -> " + products_names
    
    def extract_json(self, text):
        """Extract JSON from LLM response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1]
        return text.strip()