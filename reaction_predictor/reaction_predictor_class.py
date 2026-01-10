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
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

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
        self._process_chemistry_knowledge(self.knowledge_base)

    def _load_knowledge_base(self):
        """Load all data files from the data folder into a knowledge base string"""
        print(f"Loading knowledge base from '{DATA_PATH}' folder...")
        
        if not os.path.exists(DATA_PATH):
            print(f"Warning: Data folder '{DATA_PATH}' not found.")
            return
        
        knowledge_parts = []
        file_count = 0
        all_files = os.listdir(DATA_PATH)
        print(all_files)
        # Load all supported file types from data folder
        for filename in sorted(all_files):
            filepath = os.path.join(DATA_PATH, filename)
            content = None
            if not os.path.isfile(filepath):
                print(f"⚠ Skipping non-file entry: {filename}")
                continue
            
            try:
                if filename.endswith('.md'):
                    content = self._read_file(filepath)
                elif filename.endswith('.txt'):
                    content = self._read_file(filepath)
                elif filename.endswith('.json'):
                    content = self._read_json_file(filepath)
                elif filename.endswith('.pdf'):
                    content = self._read_pdf_file(filepath)
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
    
    def _read_pdf_file(self, filepath):
        """Read and extract text from a PDF file"""
        if PdfReader is None:
            print(f"Warning: PyPDF2 not installed. Cannot read {filepath}")
            print("Install it with: pip install PyPDF2")
            return None
        
        try:
            pdf_reader = PdfReader(filepath)
            text_content = ""
            for page_num, page in enumerate(pdf_reader.pages):
                text_content += f"\n--- Page {page_num + 1} ---\n"
                text_content += page.extract_text()
            return text_content
        except Exception as e:
            print(f"Error reading PDF file {filepath}: {e}")
            return None

    def _process_chemistry_knowledge(self, data):
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

    def analyze_reactants(self, reactants: str, reagents: str = ""):
        analyze_compound_prompt_content = self.load_prompt_template(ANALYZE_REACTANTS_PROMPT_PATH)
        analyze_compound_prompt = ChatPromptTemplate.from_template(analyze_compound_prompt_content)
        compound_analysis_prompt = analyze_compound_prompt.format(reactants=reactants, reagents=reagents)
        compound_analysis = self.model.invoke(compound_analysis_prompt)
        return compound_analysis

    def predict_reaction_products(self, reactants, reaction_conditions="", temperature=20.0):
        print("Reactants: ", reactants)
        print("Conditions: ", reaction_conditions)
        print("Temperature: ", temperature)
        # reactants_analysis = self.analyze_reactants(reactants)
        # print("Reactants analysis:\n", reactants_analysis)
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
        # embedding_function = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2"
        # )
        # print("Preparing Chroma DB for retrieval...")
        # db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        # print("Chroma DB is ready.")
        # # Search the DB.
        # results = db.similarity_search_with_relevance_scores(reactants_analysis, k=3)
        # if len(results) == 0:
        #     print(f"Unable to find matching results.")
        #     return
        
        # context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt_template = ChatPromptTemplate.from_template(prompt_template_content)
        prompt = prompt_template.format(reactants=reactants,
                                    reaction_conditions=reaction_conditions, 
                                    temperature=temperature)
        
        # print("Context used:\n", context_text)
        # print("\n" + "="*50 + "\n")
        print("Generating response...")
        response_text = self.model.invoke(prompt)

        # sources = [doc.metadata.get("source", None) for doc, _score in results]
        # formatted_response = f"Response: {response_text}\nSources: {sources}"
        # print(formatted_response)
        result = response_text.split("\n\n")
        # print("Generated reaction products:\n", result)
        return result[0]
    
    def predict_compound_visuals(self, compound, conditions="standard conditions"):
        file_path = "prompts/compound_visual_prediction_prompt.md"
        prompt = self.load_prompt_template(file_path)
        visuals_prompt = ChatPromptTemplate.from_template(prompt)
        formatted_visuals_prompt = visuals_prompt.format(compound=compound, conditions=conditions)
        visuals = self.model.invoke(formatted_visuals_prompt)
        return self.extract_json(visuals)
    
    def predict_reaction_visuals(self, reaction, products, reactant_visuals, conditions="standard conditions"):
        file_path = "prompts/reaction_visual_prediction_prompt.md"
        prompt = self.load_prompt_template(file_path)
        visuals_prompt = ChatPromptTemplate.from_template(prompt)
        formatted_visuals_prompt = visuals_prompt.format(reaction=reaction, 
                                                         products=products, 
                                                         reactant_visuals=reactant_visuals, 
                                                         conditions=conditions)
        visuals = self.model.invoke(formatted_visuals_prompt)
        return self.extract_json(visuals)
    
    def extract_json(self, text):
        """Extract JSON from LLM response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1]
        return text.strip()