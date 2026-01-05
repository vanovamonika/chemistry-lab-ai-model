from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM  # Changed this
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from . import smiles_converter
import os
import json

CHROMA_PATH = "chroma"
DATA_PATH = "data"
PROMPT_FILE_PATH = "prompts/only_products_prompt.md"
ANALYZE_REACTANTS_PROMPT_PATH = "prompts/analyze_reactants_prompt.md"
PROCESS_KNOWLEDGE_PROMPT_PATH = "prompts/process_knowledge.md"

class ReactionPredictor:
    def __init__(self):
        self.model = OllamaLLM(model="phi3:mini")
        self.knowledge_base = ""
        self._load_knowledge_base()
        self.process_chemistry_knowledge(self.knowledge_base)

    def _load_knowledge_base(self):
        """Load all data files from the data folder into a knowledge base string"""
        print(f"Loading knowledge base from '{DATA_PATH}' folder...")
        
        if not os.path.exists(DATA_PATH):
            print(f"Warning: Data folder '{DATA_PATH}' not found.")
            return
        
        knowledge_parts = []
        file_count = 0
        
        # Load all supported file types from data folder
        for filename in sorted(os.listdir(DATA_PATH)):
            filepath = os.path.join(DATA_PATH, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            try:
                if filename.endswith('.md'):
                    content = self._read_file(filepath)
                    if content:
                        knowledge_parts.append(f"\n{'='*80}\nFILE: {filename}\n{'='*80}\n{content}")
                        file_count += 1
                        print(f"✓ Loaded: {filename}")
                elif filename.endswith('.txt'):
                    content = self._read_file(filepath)
                    if content:
                        knowledge_parts.append(f"\n{'='*80}\nFILE: {filename}\n{'='*80}\n{content}")
                        file_count += 1
                        print(f"✓ Loaded: {filename}")
                elif filename.endswith('.json'):
                    content = self._read_json_file(filepath)
                    if content:
                        knowledge_parts.append(f"\n{'='*80}\nFILE: {filename}\n{'='*80}\n{content}")
                        file_count += 1
                        print(f"✓ Loaded: {filename}")
            except Exception as e:
                print(f"⚠ Error loading {filename}: {e}")
                continue
        
        # Combine all knowledge into a single string
        if knowledge_parts:
            self.knowledge_base = "".join(knowledge_parts)
            print(f"\n✓ Successfully loaded {file_count} files into knowledge base")
            print(f"Total knowledge base size: {len(self.knowledge_base)} characters")
        else:
            print("Warning: No data files were loaded")
    
    def _read_file(self, filepath):
        """Read a text or markdown file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None
    
    def _read_json_file(self, filepath):
        """Read and format a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception as e:
            print(f"Error reading JSON file {filepath}: {e}")
            return None

    def process_chemistry_knowledge(self, data):
        """Process chemistry data into a suitable format for the model"""
        prompt_content = self.load_prompt_template("prompts/process_knowledge.md")
        prompt = ChatPromptTemplate.from_template(prompt_content)
        prompt = prompt.format(knowledge=data)
        response = self.model.invoke(prompt)
        return response

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

    def analyze_reactants(self, reactants: str):
        analyze_compound_prompt_content = self.load_prompt_template(ANALYZE_REACTANTS_PROMPT_PATH)
        analyze_compound_prompt = ChatPromptTemplate.from_template(analyze_compound_prompt_content)
        compound_analysis_prompt = analyze_compound_prompt.format(reactants=reactants)
        compound_analysis = self.model.invoke(compound_analysis_prompt)
        return compound_analysis

    def predict_inorganic_reaction(self, reactants, reagents="", reaction_conditions="", temperature=20.0):
        reactants_analysis = self.analyze_reactants(reactants)

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
        model_name = "sagawa/ReactionT5v2-forward"
        
        print(f"Loading model: {model_name}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name, return_tensors="pt")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        reaction_input = f"REACTANT:{reactants}REAGENT:{reagents}"
        # Format the input properly
        # if reagents:
        #     reaction_input = f"{reactants}>{reagents}>"
        # else:
        #     reaction_input = f"{reactants}>"
        
        print(f"Predicting reaction for: {reaction_input}")
        
        # Tokenize and generate
        # input_ids = tokenizer(reaction_input, return_tensors="pt").input_ids
        
        # # Generate with reasonable parameters
        # outputs = model.generate(
        #     input_ids,
        #     max_length=100,
        #     num_beams=5,
        #     early_stopping=True,
        #     return_dict_in_generate=True,
        #     output_scores=True
        # )
        
        # # Decode the output
        # predicted_product = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)

        inp = tokenizer(reaction_input, return_tensors='pt')
        output = model.generate(**inp, num_beams=1, num_return_sequences=1, return_dict_in_generate=True, output_scores=True)
        output = tokenizer.decode(output['sequences'][0], skip_special_tokens=True).replace(' ', '').rstrip('.')
                
        return output
    
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