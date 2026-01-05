from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


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
        """Extract JSON from LLM response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1]
        return text.strip()
