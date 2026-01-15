from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json
import re


class AppearancePredictor:
    def __init__(self):
        # Configure with correct API settings
        self.model = OllamaLLM(model="phi3:mini")
        
    def load_prompt(self, type):
        prompt_files = {
            "compound": "prompts/compound_visual_prediction_prompt.md",
            "reaction": "prompts/reaction_visual_prediction_prompt.md"
        }
        file_path = prompt_files.get(type)
        if not file_path:
            raise ValueError(f"Unknown prompt type: {type}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                prompt_content = file.read()
                print(f"Loaded prompt for {type} from {file_path}")
            return prompt_content
        except FileNotFoundError:
            print(f"Error: Prompt file not found at {file_path}")
            return None
        except Exception as e:
            print(f"Error loading prompt file: {e}")
            return None
    
    def predict_visuals(self, type, reaction, conditions="standard conditions"):
        prompt = self.load_prompt(type)
        visuals_prompt = ChatPromptTemplate.from_template(prompt)
        formatted_visuals_prompt = visuals_prompt.format(reaction=reaction, conditions=conditions)
        visuals = self.model.invoke(formatted_visuals_prompt)
        # print(f"visuals:\n{visuals}")
        return self.extract_json(visuals)

    
    def extract_json(self, text):
        """Extract and parse JSON from LLM response"""
        try:
            # Remove markdown code blocks if present
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            text = text.strip()
            
            # Clean up the JSON string to fix common LLM formatting issues
            json_str = self._clean_json_string(text)
            
            # Parse the JSON string into a dictionary
            parsed_json = json.loads(json_str)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw text was: {text}")
            return {}

    def _clean_json_string(self, json_str):
        """Clean up JSON string to handle unquoted keys, comments, and trailing commas"""
        # Remove comments (everything after // on a line)
        lines = json_str.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments but keep content before the comment
            if '//' in line:
                line = line.split('//')[0]
            cleaned_lines.append(line)
        json_str = '\n'.join(cleaned_lines)
        
        # Replace single quotes with double quotes for string values
        json_str = json_str.replace("'", '"')
        
        # Remove trailing commas before } and ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Add quotes around unquoted keys
        # Match: identifier followed by : (with optional whitespace)
        json_str = re.sub(r'([{,\s])([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # Fix missing commas between properties
        # Add comma between a closing brace/bracket and a quoted key
        json_str = re.sub(r'([\]}\w"])\s+(")', r'\1, \2', json_str)
        
        # Remove any duplicate commas
        json_str = re.sub(r',\s*,', ',', json_str)
        
        return json_str
