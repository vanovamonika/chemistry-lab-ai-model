# api_server.py - TOP OF FILE
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env FIRST, before any other imports
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)

# Verify the key is loaded
api_key = os.getenv('OLLAMA_API_KEY')
if not api_key:
    print("❌ CRITICAL: OLLAMA_API_KEY not found in environment!")
    print("Please create a .env file with: OLLAMA_API_KEY=your_key_here")

import ollama
import os
import json
import re
import asyncio
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from pathlib import Path
from .dto import (
    ChemicalVisualDescription, ChemicalVisualResponse,
    CompleteReactionResponse, ProductsResponse,
    ReactionState, ReactionVisualDescription,
    SolidElements, Precipitation
)

# Prompt file paths
PROMPT_FILE_PATH = "prompts/only_equation_prompt.md"
COMPOUND_VISUAL_PROMPT_PATH = "prompts/compound_visual_prediction_prompt.md"
REACTION_VISUAL_PROMPT_PATH = "prompts/reaction_visual_prediction_prompt.md"

class OllamaReactionPredictor:
    def __init__(self, model_name: str = "phi3:mini"):
        """
        Initialize the ReactionPredictor with a single Ollama model.
        
        Args:
            model_name: The model to use for all predictions
            env_path: Optional path to .env file (default: looks for .env in current directory)
        """
        
        self.client = ollama.Client()
        self.async_client = ollama.AsyncClient()
        self.model_name = model_name
        self.available_tools = {'web_search': ollama.web_search}
        # Store prompt templates
        self.prompt_templates = {}
        self._load_all_prompt_templates()

    def _load_all_prompt_templates(self):
        """Load all prompt templates from the prompts folder"""
        prompt_files = {
            'only_equation': PROMPT_FILE_PATH,
            'compound_visual': COMPOUND_VISUAL_PROMPT_PATH,
            'reaction_visual': REACTION_VISUAL_PROMPT_PATH
        }
        
        for key, file_path in prompt_files.items():
            template = self._load_prompt_template(file_path)
            if template:
                self.prompt_templates[key] = template
                print(f"✓ Loaded prompt template: {key}")
            else:
                print(f"⚠ Warning: Could not load prompt template: {key}")

    def _load_prompt_template(self, file_path: str) -> Optional[str]:
        """Load prompt template from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Error: Prompt file not found at {file_path}")
            return None
        except Exception as e:
            print(f"Error loading prompt file: {e}")
            return None

    def _format_prompt(self, template_key: str, **kwargs) -> str:
        """
        Format a prompt template by replacing placeholders with values.
        
        Args:
            template_key: Key of the template in self.prompt_templates
            **kwargs: Placeholder values to replace in the template
        
        Returns:
            Formatted prompt string
        """
        template = self.prompt_templates.get(template_key)
        if not template:
            print(f"Warning: Template '{template_key}' not found")
            return ""
        
        formatted_prompt = template
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            formatted_prompt = formatted_prompt.replace(placeholder, str(value))
        
        return formatted_prompt

    def _parse_density(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value) if value > 0 else None
        if isinstance(value, str):
            normalized = value.strip().lower().replace('g/ml', '').replace('g/cm3', '').strip()
            if normalized in {'', 'null', 'none', 'unknown', 'n/a'}:
                return None
            try:
                parsed = float(normalized)
                return parsed if parsed > 0 else None
            except ValueError:
                return None
        return None
    
    
    
    # ==================== MAIN REACTION PREDICTION ====================

    async def predict_reaction(self, reactants: str, reactant_visuals: str,
                              reaction_conditions: str = "", temperature: float = 20.0) -> CompleteReactionResponse:
        print(f"🎯 predict_reaction called with: reactants={reactants}, conditions={reaction_conditions}, temp={temperature}")
        
        try:
            # Step 1: Predict products
            print("📦 Step 1: Predicting products...")
            products_response = await self.predict_products(
                reactants=reactants,
                conditions=reaction_conditions,
                temperature=temperature
            )
            
            if not products_response.success:
                print(f"❌ Products prediction failed: {products_response.error}")
                return CompleteReactionResponse(
                    success=False,
                    reactants=reactants,
                    products=[],
                    equation="",
                    visual_description={},
                    error=f"Products prediction failed: {products_response.error}"
                )
            
            print(f"✅ Products predicted: {products_response.products}")
            print(f"✅ Equation: {products_response.equation}")
            
            # Step 2: Parse reactant visuals (if provided)
            reactant_visuals_dict = {}
            if reactant_visuals:
                try:
                    reactant_visuals_dict = json.loads(reactant_visuals)
                    print(f"✅ Parsed reactant visuals: {reactant_visuals_dict}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Could not parse reactant_visuals JSON: {e}")
                    reactant_visuals_dict = {"error": "Invalid JSON", "raw": reactant_visuals}
            
            # Step 3: Predict reaction visuals
            print("🎨 Step 3: Predicting reaction visuals...")
            visual_description = await self.predict_reaction_visuals(
                reaction=products_response.equation,
                products=products_response.products,
                reactant_visuals=reactant_visuals_dict,
                conditions=reaction_conditions
            )
            
            print(f"✅ Visuals predicted: {visual_description}")
            
            # Step 4: Convert visual_description to dict for response
            # visual_dict = visual_description.model_dump()
            
            # Step 5: Return complete response
            return CompleteReactionResponse(
                success=True,
                reactants=reactants,
                products=products_response.products,
                equation=products_response.equation,
                visual_description=visual_description,
                error=None
            )
            
        except Exception as e:
            print(f"❌ Error in predict_reaction: {e}")
            import traceback
            traceback.print_exc()
            
            return CompleteReactionResponse(
                success=False,
                reactants=reactants,
                products=[],
                equation="",
                visual_description={},
                error=str(e)
            )

    # ==================== PRODUCTS PREDICTION (USING CHAT) ====================

    async def predict_products(self, reactants: str, 
                              conditions: str = "", 
                              temperature: float = 20.0) -> ProductsResponse:
        try:
            # Step 1: Perform web search
            search_query = f"{reactants} reaction products under {conditions}".strip()
            print(f"🔍 Searching web for: {search_query}")
            
            search_results = ollama.web_search(search_query, max_results=5)
            
            # Step 2: Format search results
            search_context = "Web search results:\n\n"
            for i, result in enumerate(search_results.get('results', [])[:3], 1):
                search_context += f"{i}. {result.get('title', 'Untitled')}\n"
                search_context += f"   {result.get('content', '')[:500]}...\n\n"
            
            # Step 3: Get base prompt and enhance with search results
            base_prompt = self._format_prompt('only_equation', 
                                              reactants=reactants,
                                              reaction_conditions=conditions,
                                              temperature=temperature)
            
            if not base_prompt:
                base_prompt = f"Predict the products of this chemical reaction: {reactants} at {temperature}°C under {conditions}"
            
            # Step 4: Use chat API with system and user messages
            messages = [
                
                {
                    "role": "user", 
                    "content": f"{base_prompt} \nUSE THESE ADDITIONAL INFORMATION FROM WEB SEARCH:\n{search_context}"
                }
            ]
            
            response = await self.async_client.chat(
                model=self.model_name,
                messages=messages
            )
            
            response_text = response.message.content
            print(f"✅ Products response received: {response_text[:100]}...")
            
            # Step 5: Parse response
            parts = re.split(r'[;\n]', response_text)
            equation = parts[0].strip() if parts else ""
            products = self._extract_products(parts[0]) if parts else []
            
            return ProductsResponse(
                success=True,
                reactants=reactants,
                products=products,
                equation=equation,
                generated_response=response_text
            )
            
        except Exception as e:
            print(f"❌ Error in predict_products: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = str(e)
            if "Authorization" in error_msg or "401" in error_msg:
                error_msg = "Invalid API key. Please check your OLLAMA_API_KEY in .env"
            
            return ProductsResponse(
                success=False,
                reactants=reactants,
                products=[],
                equation="",
                generated_response="",
                error=error_msg
            )

    def _extract_products(self, text: str) -> List[str]:
        """Extract clean product formulas from reaction equation"""
        try:
            # Split by reaction arrow
            parts = re.split(r'->|→|=>|⇌', text)
            if len(parts) < 2:
                return []
            
            products_part = parts[1].strip()
            
            if "No Reaction" in products_part:
                return ["No Reaction"]
            
            # Split by + and clean each product
            products = []
            for prod in products_part.split(" + "):
                prod = prod.strip()
                # Remove state symbols
                prod = re.sub(r'\([a-z]+\)$', '', prod)
                # Remove coefficients
                prod = re.sub(r'^\d+', '', prod)
                if prod:
                    products.append(prod)
            
            return products
            
        except Exception as e:
            print(f"Error extracting products: {e}")
            return []

    # ==================== COMPOUND VISUALS PREDICTION (USING CHAT) ====================

    async def predict_compound_visuals(self, formula: str, 
                                      name: Optional[str] = None,
                                      conditions: str = "standard conditions") -> ChemicalVisualResponse:
        try:
            # compound_display = name if name else formula
            search_query = f"{name} ({formula}) color state solubility"
            print(f"🔍 Searching web for: {search_query}")
            
            search_results = ollama.web_search(search_query, max_results=3)
            print(f"✅ Web search completed for compound visuals")
            # Step 2: Format search results
            search_context = "Web search results:\n\n"
            for result in search_results.results:  # 'results' is a list
                search_context += f"Title: {result.title}\n"
                search_context += f"URL: {result.url}\n"
                search_context += f"Content: {result.content}...\n\n"
            print(f"🔍 Search context extracted: {search_context[:1000]}")
            # Step 3: Get base prompt and enhance
            base_prompt = self._format_prompt('compound_visual',
                                              formula=formula,
                                              name=name if name else formula,
                                              conditions=conditions)
            
            if not base_prompt:
                base_prompt = f"Describe the visual properties of {formula} ({name if name else 'unknown'}) at {conditions}"
            print(f"✅ Base prompt prepared: {base_prompt[:1000]}...")  # Print first 200 chars
            # Step 4: Use chat API
            # messages = [
            #     {
            #         "role": "system",
            #         "content": "You are a chemistry expert. Always respond with valid JSON only."
            #     },
            #     {
            #         "role": "user",
            #         "content": f"{base_prompt}\nUSE ADDITIONAL INFORMATION FROM WEB SEARCH:\n{search_context}"
            #     }
            # ]
            
            # response = await self.async_client.chat(
            #     model=self.model_name,
            #     messages=[
            #         {
            #             "role": "system",
            #             "content": "You are a chemistry expert. Always respond with valid JSON only."
            #         },
            #         {
            #             "role": "user",
            #             "content": base_prompt + "\n\nuse these information retrieved from a web search:\n" + search_context
            #         }
            #     ]
            # )

            try:
                # Set a timeout of 30 seconds
                response = await asyncio.wait_for(
                    self.async_client.chat(
                        model=self.model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a chemistry expert. Always respond with valid JSON only."
                            },
                            {
                                "role": "user",
                                "content": base_prompt + "\n\nuse these information retrieved from a web search:\n" + search_context
                            }
                        ]
                    ),
                    timeout=60.0  # 30 seconds timeout
                )
                
                # If we get here, the response completed within 30 seconds
                print("✅ Response received within timeout")
                
            except asyncio.TimeoutError:
                print("❌ Request timed out after 30 seconds")
                # Handle timeout gracefully - return default response
                return ChemicalVisualResponse(
                    success=False,
                    formula=formula,
                    name=name or formula,
                    visual_description=ChemicalVisualDescription(
                        color_hex="#ffffff",
                        color="unknown",
                        state="unknown",
                        soluble_in_water=False,
                        density=None
                    ),
                    error="Request timed out after 30 seconds"
                )

            print(f"✅ Compound visuals response received: {response.message.content}")
            
            response_text = response.message.content
            print(f"✅ Compound visuals response received: {response_text}")
            
            # Step 5: Extract and validate JSON
            # json_data = self._extract_json(response_text)
            json_data = json.loads(response_text)
            print(f"✅ Extracted JSON data: {json_data}")
            
            # Step 6: Create description with defaults
            visual_desc = ChemicalVisualDescription(
                color_hex=json_data.get('color_hex', '#ffffff'),
                color=json_data.get('color', 'unknown'),
                state=json_data.get('state', 'unknown'),
                soluble_in_water=self._parse_solubility(json_data.get('soluble_in_water', True)),
                density=self._parse_density(json_data.get('density'))
            )
            
            return ChemicalVisualResponse(
                success=True,
                formula=formula,
                name=name or formula,
                visual_description=visual_desc
            )
            
        except Exception as e:
            print(f"❌ Error in predict_compound_visuals: {e}")
            import traceback
            traceback.print_exc()
            
            return ChemicalVisualResponse(
                success=False,
                formula=formula,
                name=name or formula,
                visual_description=ChemicalVisualDescription(
                    color_hex="#ffffff",
                    color="unknown",
                    state="unknown",
                    soluble_in_water=False,
                    density=None
                ),
                error=str(e)
            )

    def _parse_solubility(self, soluble: Any) -> bool:
        """Parse solubility value to boolean"""
        if soluble is None:
            return False
        if isinstance(soluble, bool):
            return soluble
        if isinstance(soluble, str):
            return soluble.lower() in ['true', 'yes', 'soluble', '1']
        return bool(soluble)

    # ==================== REACTION VISUALS PREDICTION (USING CHAT) ====================

    async def predict_reaction_visuals(self, reaction: str, 
                                      products: List[str],
                                      reactant_visuals: Dict,
                                      conditions: str = "standard conditions") -> ReactionVisualDescription:
        """
        Predict visual changes during a reaction using web search with chat API.
        
        Args:
            reaction: The balanced reaction equation
            products: List of product formulas
            reactant_visuals: Visual properties of reactants
            conditions: Reaction conditions
        
        Returns:
            ReactionVisualDescription with before/during/after states
        """
        try:
            # Check API key first
            # if not self._ensure_api_key():
            #     return self._create_default_reaction_visuals()
            
            # Step 1: Perform web search
            search_query = f"{reaction} color change appearance reaction"
            print(f"🔍 Searching web for: {search_query}")
            
            search_results = ollama.web_search(search_query, max_results=5)
            
            # Step 2: Format search results
            search_context = "Web search results:\n\n"
            for i, result in enumerate(search_results.get('results', [])[:3], 1):
                search_context += f"{i}. {result.get('title', 'Untitled')}\n"
                search_context += f"   {result.get('content', '')[:500]}...\n\n"
            
            # Step 3: Get base prompt and enhance
            base_prompt = self._format_prompt('reaction_visual',
                                              reaction=reaction,
                                              products=str(products),
                                              reactant_visuals=json.dumps(reactant_visuals),
                                              conditions=conditions)
            
            if not base_prompt:
                base_prompt = f"Describe the visual changes during this reaction: {reaction}"
            
            # Step 4: Use chat API
            messages = [
                # {
                #     "role": "system",
                #     "content": "You are a chemistry expert. Based on web search results, describe the visual changes during chemical reactions accurately. Always respond with valid JSON."
                # },
                {
                    "role": "user",
                    "content": f"""{base_prompt}\nUSE ADDITIONAL INFORMATION FROM WEB SEARCH:\n{search_context}"""
                }
            ]
            
            response = await self.async_client.chat(
                model=self.model_name,
                messages=messages
            )
            
            response_text = response.message.content
            print(f"✅ Reaction visuals response received")
            
            # Step 5: Extract and validate JSON
            json_data = self._extract_json(response_text)
            
            # Step 6: Create ReactionVisualDescription with defaults
            return self._create_reaction_visuals_from_json(json_data)
            
        except Exception as e:
            print(f"❌ Error in predict_reaction_visuals: {e}")
            import traceback
            traceback.print_exc()
            
            return self._create_default_reaction_visuals()

    def _create_reaction_visuals_from_json(self, json_data: Dict) -> ReactionVisualDescription:
        """Create ReactionVisualDescription from parsed JSON with defaults"""
        
        # Default state
        default_state = {
            "color_hex": "#000000",
            "color": "unknown",
            "state": "unknown",
            "solid_elements": {"color_hex": "#000000", "color": "unknown"},
            "bubbles": False,
            "precipitation": {"color_hex": "#000000", "color": "unknown"}
        }
        
        def get_state(state_key):
            state_data = json_data.get(state_key, {})
            if not isinstance(state_data, dict):
                return default_state.copy()
            
            return {
                "color_hex": state_data.get('color_hex', default_state['color_hex']),
                "color": state_data.get('color', default_state['color']),
                "state": state_data.get('state', default_state['state']),
                "solid_elements": {
                    "color_hex": state_data.get('solid_elements', {}).get('color_hex', 
                                                                          default_state['solid_elements']['color_hex']),
                    "color": state_data.get('solid_elements', {}).get('color', 
                                                                      default_state['solid_elements']['color'])
                },
                "bubbles": state_data.get('bubbles', default_state['bubbles']),
                "precipitation": {
                    "color_hex": state_data.get('precipitation', {}).get('color_hex', 
                                                                         default_state['precipitation']['color_hex']),
                    "color": state_data.get('precipitation', {}).get('color', 
                                                                     default_state['precipitation']['color'])
                }
            }
        
        # Create SolidElements and Precipitation objects
        middle_state = get_state('middle_of_reaction')
        final_state = get_state('final_state')
        
        middle = ReactionState(
            color_hex=middle_state["color_hex"],
            color=middle_state["color"],
            state=middle_state["state"],
            solid_elements=SolidElements(
                color_hex=middle_state["solid_elements"]["color_hex"],
                color=middle_state["solid_elements"]["color"]
            ),
            bubbles=middle_state["bubbles"],
            precipitation=Precipitation(
                color_hex=middle_state["precipitation"]["color_hex"],
                color=middle_state["precipitation"]["color"]
            )
        )
        
        final = ReactionState(
            color_hex=final_state["color_hex"],
            color=final_state["color"],
            state=final_state["state"],
            solid_elements=SolidElements(
                color_hex=final_state["solid_elements"]["color_hex"],
                color=final_state["solid_elements"]["color"]
            ),
            bubbles=final_state["bubbles"],
            precipitation=Precipitation(
                color_hex=final_state["precipitation"]["color_hex"],
                color=final_state["precipitation"]["color"]
            )
        )
        
        return ReactionVisualDescription(
            middle_of_reaction=middle,
            final_state=final,
            timing=json_data.get('timing', 'unknown')
        )

    def _create_default_reaction_visuals(self) -> ReactionVisualDescription:
        """Create default reaction visuals for error cases"""
        default_solid = SolidElements(color_hex="#000000", color="unknown")
        default_precip = Precipitation(color_hex="#000000", color="unknown")
        
        default_state = ReactionState(
            color_hex="#000000",
            color="unknown",
            state="unknown",
            solid_elements=default_solid,
            bubbles=False,
            precipitation=default_precip
        )
        
        return ReactionVisualDescription(
            middle_of_reaction=default_state,
            final_state=default_state,
            timing="unknown"
        )

    # ==================== UTILITY FUNCTIONS ====================

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response and parse it"""
        try:
            # Remove markdown code blocks
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            text = text.strip()
            
            # Clean the JSON string
            json_str = self._clean_json_string(text)
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error extracting JSON: {e}")
            return {}

    def _clean_json_string(self, json_str: str) -> str:
        """Clean up JSON string to handle common formatting issues"""
        # Remove comments
        lines = json_str.split('\n')
        cleaned_lines = []
        for line in lines:
            if '//' in line:
                line = line.split('//')[0]
            cleaned_lines.append(line)
        json_str = '\n'.join(cleaned_lines)
        
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')
        
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Add quotes around unquoted keys
        json_str = re.sub(r'([{,\s])([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        return json_str