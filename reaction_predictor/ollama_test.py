import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path
from .helpers import extract_products, parse_solubility, get_formatted_prompt, extract_json
import re
from .dto import ChemicalVisualDescription, ChemicalVisualResponse, Precipitation, ProductsResponse, ReactionState, ReactionVisualDescription, SolidElements
# import helpers

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
model_name = "phi3:mini"  # Ensure this matches your Ollama model name
async_client = ollama.AsyncClient()

async def predict_products(reactants: str, conditions: str = "", temperature: float = 20.0) -> ProductsResponse:
        try:
            # Step 1: Perform web search
            search_query = f"{reactants} reaction products under {conditions} at {temperature}°C".strip()
            print(f"🔍 Searching web for: {search_query}")
            
            search_results = ollama.web_search(search_query, max_results=3)
            
            # Step 2: Format search results
            # search_context = "Web search results:\n\n"
            # for i, result in enumerate(search_results.get('results', [])[:3], 1):
            #     search_context += f"{i}. {result.get('title', 'Untitled')}\n"
            #     search_context += f"   {result.get('content', '')[:500]}...\n\n"
            search_context = "Web search results:\n\n"
            for result in search_results.results:  # 'results' is a list
                search_context += f"Title: {result.title}\n"
                search_context += f"URL: {result.url}\n"
                search_context += f"Content: {result.content[:1000]}...\n\n"
            # Step 3: Get base prompt and enhance with search results
            base_prompt = get_formatted_prompt('prompts/only_equation_prompt.md', 
                                              reactants=reactants,
                                              reaction_conditions=conditions,
                                              temperature=temperature)
            
            if not base_prompt or base_prompt == "":
                base_prompt = f"Predict the products of this chemical reaction: {reactants} at {temperature}°C under {conditions}"
            
            # Step 4: Use chat API with system and user messages
            # messages = [
                
            #     {
            #         "role": "user", 
            #         "content": f"{base_prompt} \nUSE THESE ADDITIONAL INFORMATION FROM WEB SEARCH:\n{search_context}"
            #     }
            # ]
            
            # response = await async_client.chat(
            #     model=model_name,
            #     messages=messages
            # )

            try:
                start_time = time.time()
                response = await asyncio.wait_for(
                    async_client.chat(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a chemistry expert. Always respond only in the format specified in the prompt."
                            },
                            {
                                "role": "user", 
                                "content": f"{base_prompt} \nUSE THESE ADDITIONAL INFORMATION FROM WEB SEARCH:\n{search_context}"
                            }
                        ]
                    ),
                    timeout=120.0 
                )
                total_time = time.time() - start_time
                print(f"✅ Response received in {total_time}")
                
            except asyncio.TimeoutError:
                print("❌ Request timed out after 120 seconds")
                return ProductsResponse(
                    success=False,
                    reactants=reactants,
                    products=[],
                    equation="",
                    error="Request timed out after 120 seconds"
                )
            
            response_text = response.message.content
            print(f"✅ Products response received: {response_text[:100]}...")
            
            # Step 5: Parse response
            parts = re.split(r'[;\n]', response_text)
            equation = parts[0].strip() if parts else ""
            products = extract_products(parts[0]) if parts else []
            
            return ProductsResponse(
                success=True,
                reactants=reactants,
                products=products,
                equation=equation,
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
                error=error_msg
            )

async def predict_compound_visuals(formula: str, name: str, conditions: str = "standard conditions") -> ChemicalVisualResponse:
        try:
            compound_display = name if name else formula
            search_query = f"{compound_display} chemical physical properties color state solubility"
            
            
            search_results = ollama.web_search(search_query, max_results=3)
            
            # Step 2: Format search results
            search_context = "Web search results:\n\n"
            for result in search_results.results:  # 'results' is a list
                search_context += f"Title: {result.title}\n"
                search_context += f"URL: {result.url}\n"
                search_context += f"Content: {result.content[:1000]}...\n\n"
            print(f"🔍 Searching web for: {search_query}: {search_context}")
            base_prompt = get_formatted_prompt('prompts/compound_visual_prediction_prompt.md',
                                              formula=formula,
                                              name=name if name else formula,
                                              conditions=conditions)
            
            print(f"✅ Base prompt prepared: {base_prompt[:1000]}...")  # Print first 200 chars
            if not base_prompt or base_prompt == "":
                base_prompt = f"Describe the visual properties of {formula} ({name if name else 'unknown'}) at {conditions}"
            
            # Step 4: Use chat API
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(
                    async_client.chat(
                        model=model_name,
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
                    timeout=120.0  
                )
                total_time = time.time() - start_time
                print(f"✅ Response received in {total_time}")
                
            except asyncio.TimeoutError:
                print("❌ Request timed out after 120 seconds")
                return ChemicalVisualResponse(
                    success=False,
                    formula=formula,
                    name=name or formula,
                    visual_description=ChemicalVisualDescription(
                        color_hex="#ffffff",
                        color="unknown",
                        state="unknown",
                        soluble_in_water=False
                    ),
                    error="Request timed out after 120 seconds"
                )

            print(f"✅ Compound visuals response received: {response}")
            
            response_text = response.message.content
            print(f"✅ Compound visuals response received: {response_text}")
            
            # Step 5: Extract and validate JSON
            json_data = extract_json(response_text)
            print(json_data)
            if json_data == {}:
                print("using json loads")
                json_data = json.loads(response_text)
            print(f"✅ Extracted JSON data: {json_data}")
            
            # Step 6: Create description with defaults
            visual_desc = ChemicalVisualDescription(
                color_hex=json_data.get('color_hex', '#ffffff'),
                color=json_data.get('color', 'unknown'),
                state=json_data.get('state', 'unknown'),
                soluble_in_water=parse_solubility(json_data.get('soluble_in_water', True))
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
                    soluble_in_water=False
                ),
                error=str(e)
            )