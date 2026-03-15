import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv
from pathlib import Path
from .helpers import (
    color_name_to_hex,
    extract_products,
    parse_solubility,
    get_formatted_prompt,
    extract_json,
    normalize_equation_line,
    validate_reaction_output,
)
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

MAX_PARALLEL_CHATS = max(1, int(os.getenv("OLLAMA_MAX_PARALLEL_CHATS", "2")))
MAX_PARALLEL_CHEMICALS = max(1, int(os.getenv("OLLAMA_MAX_PARALLEL_CHEMICALS", "2")))
_chat_semaphore = asyncio.Semaphore(MAX_PARALLEL_CHATS)
_chemical_semaphore = asyncio.Semaphore(MAX_PARALLEL_CHEMICALS)


def _error_details(e: Exception) -> str:
    message = str(e).strip()
    return message if message else repr(e)


async def _chat_with_retry(messages: List[Dict[str, str]], timeout: float, retries: int = 1) -> Any:
    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 2):
        try:
            async with _chat_semaphore:
                return await asyncio.wait_for(
                    async_client.chat(
                        model=model_name,
                        messages=messages,
                    ),
                    timeout=timeout,
                )
        except Exception as e:
            last_error = e
            if attempt <= retries:
                await asyncio.sleep(min(2.5, 0.5 * attempt))
            else:
                break

    raise last_error if last_error else RuntimeError("Unknown chat failure")


def _build_search_context(search_results: Any, content_limit: int = 1000) -> str:
    context = "Web search results:\n\n"
    for result in getattr(search_results, "results", []) or []:
        context += f"Title: {getattr(result, 'title', '')}\n"
        context += f"URL: {getattr(result, 'url', '')}\n"
        context += f"Content: {str(getattr(result, 'content', ''))[:content_limit]}...\n\n"
    return context


def _safe_web_search_context(query: str, max_results: int = 3, content_limit: int = 1000) -> str:
    try:
        search_results = ollama.web_search(query, max_results=max_results)
        return _build_search_context(search_results, content_limit=content_limit)
    except Exception as e:
        print(f"⚠️ Web search unavailable for query '{query}': {_error_details(e)}")
        return "Web search results:\n\n(No web results available)\n"

def parse_density(value: Any) -> Optional[float]:
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

def parse_numeric_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        parsed = float(value)
        return parsed if parsed > 0 else None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'', 'null', 'none', 'unknown', 'n/a', 'not available'}:
            return None
        # Keep only first numeric token (supports scientific notation)
        # match = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', normalized)
        parts = normalized.split()
        for part in parts:
            try:
                return float(part) if float(part) > 0 else None
            except ValueError:
                continue
    return None

async def _predict_single_numeric_property(
    formula: str,
    name: str,
    property_name: str,
    unit_hint: str,
) -> Optional[float]:
        try:
            compound_display = name if name else formula
            search_query = f"{compound_display} ({formula}) {property_name} {unit_hint}".strip()
            search_context = _safe_web_search_context(search_query, max_results=1, content_limit=1000)

            prompt = (
                f"Find the {property_name} of {compound_display} ({formula}). "
                f"Return ONLY one number in {unit_hint}. "
                f"If unknown, return exactly: null\n\n"
                f"Use this context:\n{search_context}"
            )

            response = await _chat_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a chemistry expert. Return only one numeric value or null.",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=70.0,
                retries=1,
            )

            raw = response.message.content.strip()
            parsed = parse_numeric_value(raw)
            print(f"📏 Parsed {property_name} for {formula}: raw='{raw}' -> {parsed}")
            return parsed
        except Exception as e:
            print(f"⚠️ Failed to predict {property_name} for {formula}: {_error_details(e)}")
            return None

async def predict_density(formula: str, name: str, conditions: str = "standard conditions") -> Optional[float]:
        _ = conditions
        return await _predict_single_numeric_property(formula, name, "density", "g/cm3")

async def predict_molar_mass(formula: str, name: str, conditions: str = "standard conditions") -> Optional[float]:
        _ = conditions
        return await _predict_single_numeric_property(formula, name, "molar mass", "g/mol")


def _looks_like_formula(value: str) -> bool:
        token = (value or "").strip()
        if not token:
            return True
        # Common formula-like patterns, e.g. H2O, NaCl, Fe2O3, NH4NO3
        return re.fullmatch(r"[A-Z][A-Za-z0-9()\[\]·\.+\-^]*", token) is not None


async def predict_compound_name(formula: str, name: str = "") -> str:
        """Predict a canonical/common compound name from a formula."""
        try:
            normalized_name = (name or "").strip()
            placeholder_names = {"unknown", "name unknown", "n/a", "none", "null"}
            if (
                normalized_name
                and normalized_name.lower() not in placeholder_names
                and not _looks_like_formula(normalized_name)
            ):
                return normalized_name

            search_query = f"{formula} chemical compound name"
            search_context = _safe_web_search_context(search_query, max_results=3, content_limit=800)

            prompt = (
                f"Determine the standard/common English name for the chemical formula '{formula}'. "
                "Return ONLY the compound name as plain text. "
                "Do not include formula, punctuation, explanations, or multiple options."
            )

            response = await _chat_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a chemistry expert. Return only one compound name as plain text.",
                    },
                    {
                        "role": "user",
                        "content": prompt + "\n\nUse this context:\n" + search_context,
                    },
                ],
                timeout=60.0,
                retries=1,
            )

            raw_name = (response.message.content or "").strip()
            raw_name = re.sub(r"^['\"\s]+|['\"\s]+$", "", raw_name)
            raw_name = re.sub(r"\s+", " ", raw_name)

            if not raw_name or _looks_like_formula(raw_name) or len(raw_name) > 120:
                return formula

            return raw_name
        except Exception as e:
            print(f"⚠️ Failed to predict compound name for {formula}: {_error_details(e)}")
            return formula


def _normalize_chemical_input(chemical: Union[str, Dict[str, Any]]) -> Tuple[str, str, str]:
        """
        Normalize one chemical item into (formula, name, conditions).

        Supported formats:
        - "H2O"
        - {"formula": "H2O", "name": "water", "conditions": "standard conditions"}
        """
        if isinstance(chemical, str):
            formula = chemical.strip()
            return formula, formula, "standard conditions"

        if isinstance(chemical, dict):
            formula = str(chemical.get("formula", "")).strip()
            name = str(chemical.get("name", "")).strip() or formula
            conditions = str(chemical.get("conditions", "standard conditions")).strip() or "standard conditions"
            return formula, name, conditions

        raise ValueError(f"Unsupported chemical item type: {type(chemical).__name__}")

async def predict_products(reactants: str, conditions: str = "", temperature: float = 20.0) -> ProductsResponse:
        try:
            max_attempts = 3
            last_validation_error = ""
            strict_instruction = (
                "Return ONLY one balanced equation. "
                "Do not include URLs, references, citations, markdown, or explanatory text. "
                "Each product must be a valid chemical formula."
            )

            for attempt in range(1, max_attempts + 1):
                search_query = f"{reactants} reaction products under {conditions} at {temperature}°C".strip()
                if attempt > 1:
                    search_query += " verified balanced chemical equation"

                print(f"🔍 [Attempt {attempt}/{max_attempts}] Searching web for: {search_query}")
                search_results = ollama.web_search(search_query, max_results=3)

                search_context = "Web search results:\n\n"
                for result in search_results.results:
                    search_context += f"Title: {result.title}\n"
                    search_context += f"URL: {result.url}\n"
                    search_context += f"Content: {result.content[:1000]}...\n\n"

                base_prompt = get_formatted_prompt(
                    'prompts/only_equation_prompt.md',
                    reactants=reactants,
                    reaction_conditions=conditions,
                    temperature=temperature
                )

                if not base_prompt:
                    base_prompt = f"Predict the products of this chemical reaction: {reactants} at {temperature}°C under {conditions}"

                retry_guardrail = ""
                if attempt > 1:
                    retry_guardrail = (
                        f"\n\nPrevious output was invalid ({last_validation_error}). "
                        "Regenerate strictly as a clean chemical equation only."
                    )

                try:
                    start_time = time.time()
                    response = await asyncio.wait_for(
                        async_client.chat(
                            model=model_name,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a chemistry expert. "
                                        "Always respond only in the format specified in the prompt. "
                                        #f"{strict_instruction}"
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": base_prompt + "\n\nuse these information retrieved from a web search:\n" + search_context
                                    + retry_guardrail}
                            ]
                        ),
                        timeout=180.0
                    )
                    total_time = time.time() - start_time
                    print(f"✅ Response received in {total_time}")

                except asyncio.TimeoutError:
                    print("❌ Request timed out after 180 seconds")
                    last_validation_error = "Request timed out after 180 seconds"
                    continue

                response_text = response.message.content
                print(f"✅ Products response received: {response_text[:100]}...")

                equation = normalize_equation_line(response_text)
                products = extract_products(equation) if equation else []

                is_valid, reason, cleaned_products, cleaned_equation = validate_reaction_output(equation, products)

                if is_valid:
                    return ProductsResponse(
                        success=True,
                        reactants=reactants,
                        products=cleaned_products,
                        equation=cleaned_equation,
                    )

                last_validation_error = reason
                print(f"⚠️ Invalid products/equation output on attempt {attempt}: {reason}")

            return ProductsResponse(
                success=False,
                reactants=reactants,
                products=[],
                equation="",
                error=f"Failed to generate chemically valid products after {max_attempts} attempts: {last_validation_error or 'Unknown validation error'}"
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

async def predict_compound_visuals(
    formula: str,
    name: str,
    conditions: str = "standard conditions",
    include_density_and_name: bool = True,
) -> ChemicalVisualResponse:
        try:
            compound_display = name if name else formula
            search_query = f"{compound_display} chemical physical properties color state solubility"
            search_context = _safe_web_search_context(search_query, max_results=3, content_limit=1000)
            # print(f"🔍 Searching web for: {search_query}: {search_context}")

            density_task = None
            if include_density_and_name:
                density_task = asyncio.create_task(predict_density(formula, name, conditions))

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
                response = await _chat_with_retry(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a chemistry expert. Always respond with valid JSON only."
                        },
                        {
                            "role": "user",
                            "content": base_prompt + "\n\nuse these information retrieved from a web search:\n" + search_context
                        }
                    ],
                    timeout=150.0,
                    retries=1,
                )
                total_time = time.time() - start_time
                print(f"✅ Response received in {total_time}")

            except Exception as e:
                print(f"❌ Visual prediction failed for {formula}: {_error_details(e)}")
                return ChemicalVisualResponse(
                    success=False,
                    formula=formula,
                    name=name or formula,
                    visual_description=ChemicalVisualDescription(
                        color_hex="#ffffff",
                        color="unknown",
                        state="unknown",
                        soluble_in_water=False,
                        density=None,
                        molar_mass=None
                    ),
                    error=f"Visual prediction failed: {_error_details(e)}"
                )

            print(f"✅ Compound visuals response received: {response}")
            
            response_text = response.message.content
            print(f"✅ Compound visuals response received: {response_text}")
            
            # Step 5: Extract and validate JSON
            try:
                json_data = extract_json(response_text)
            except Exception as parse_error:
                print(f"⚠️ Failed to extract JSON from model output: {parse_error}")
                json_data = {}
            print(json_data)
            if not json_data:
                print("⚠️ No valid JSON found in model output, using safe defaults for visual fields")
                json_data = {
                    'color_hex': '#ffffff',
                    'color': 'unknown',
                    'state': 'unknown',
                    'soluble_in_water': False,
                }
            print(f"✅ Extracted JSON data: {json_data}")

            predicted_density = None
            # Resolve name from JSON response (same prompt, no extra Ollama call needed)
            json_name = (json_data.get('name') or '').strip()
            placeholder_names = {'unknown', 'name unknown', 'n/a', 'none', 'null', ''}
            if json_name and json_name.lower() not in placeholder_names and not _looks_like_formula(json_name) and len(json_name) <= 120:
                predicted_name = json_name
            elif name and (name or '').lower() not in placeholder_names and not _looks_like_formula(name):
                predicted_name = name
            else:
                predicted_name = formula
            if density_task:
                density_result = await asyncio.gather(density_task, return_exceptions=True)
                predicted_density = None if isinstance(density_result[0], Exception) else density_result[0]
            fallback_hex = color_name_to_hex(json_data.get('color', 'unknown'))
            if json_data.get('color_hex') in {None, '', 'null', 'none', 'unknown'}:
                json_data['color_hex'] = fallback_hex
            # Step 6: Create description with defaults
            visual_desc = ChemicalVisualDescription(
                color_hex=json_data.get('color_hex', '#ffffff'),
                color=json_data.get('color', 'unknown'),
                state=json_data.get('state', 'unknown'),
                soluble_in_water=parse_solubility(json_data.get('soluble_in_water', True)),
                density=predicted_density,
                molar_mass=None
            )
            
            return ChemicalVisualResponse(
                success=True,
                formula=formula,
                name=predicted_name or name or formula,
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
                    density=None,
                    molar_mass=None
                ),
                error=str(e)
            )

async def get_all_chemical_data(chemicals):
    async def _collect_one(chemical: Union[str, Dict[str, Any]]) -> ChemicalVisualResponse:
        try:
            formula, provided_name, conditions = _normalize_chemical_input(chemical)

            async with _chemical_semaphore:
                # Single orchestrated call per chemical to reduce overload and timeout risk.
                return await predict_compound_visuals(
                    formula=formula,
                    name=provided_name,
                    conditions=conditions,
                    include_density_and_name=True,
                )
        except Exception as e:
            fallback_formula = (
                chemical.strip() if isinstance(chemical, str) else str(chemical.get("formula", ""))
            )
            fallback_formula = fallback_formula or "unknown"
            return ChemicalVisualResponse(
                success=False,
                formula=fallback_formula,
                name=fallback_formula,
                visual_description=ChemicalVisualDescription(
                    color_hex="#ffffff",
                    color="unknown",
                    state="unknown",
                    soluble_in_water=False,
                    density=None,
                    molar_mass=None,
                ),
                error=_error_details(e),
            )

    # Run all chemicals concurrently.
    tasks = [_collect_one(chemical) for chemical in chemicals]
    return await asyncio.gather(*tasks)