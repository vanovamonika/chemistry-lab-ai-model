import argparse
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM  # Changed this
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate

CHROMA_PATH = "chroma"

PROMPT_FILE_PATH = "prompts/only_products_prompt.md"

def load_prompt_template(file_path):
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

def main(reactants: str, reagents: str = "", reaction_conditions: str = "", temperature: float = 20.0):

    query_text = f"Reactants: {reactants}\nReagents: {reagents}\nConditions: {reaction_conditions}\nTemperature: {temperature}°C"

    # Load the prompt template
    prompt_template_content = load_prompt_template(PROMPT_FILE_PATH)
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
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0:
        print(f"Unable to find matching results.")
        return

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(prompt_template_content)
    prompt = prompt_template.format(reactants=reactants, reagents=reagents,
                                   reaction_conditions=reaction_conditions, 
                                   temperature=temperature, context=context_text, question=query_text)
    print("Context used:\n", context_text)
    print("\n" + "="*50 + "\n")

    # Use Ollama with Mistral
    model = OllamaLLM(model="mistral:7b-instruct")
    
    print("Generating response...")
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("source", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)

if __name__ == "__main__":
    main()