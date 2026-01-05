# from langchain.document_loaders import DirectoryLoader
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings  # Changed this line
# from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import shutil
import os
import dotenv

CHROMA_PATH = "chroma"
DATA_PATH = dotenv.get_key(dotenv.find_dotenv(), "DATA_PATH") or "data"

def main():
    generate_data_store()

def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

# def load_documents():
#     loader = DirectoryLoader(DATA_PATH, glob="*.md")
#     documents = loader.load()
#     return documents

def load_documents():
    # Method 1A: Using multiple glob patterns
    loader = DirectoryLoader(
        DATA_PATH, 
        glob="**/*.md",  # Load all markdown files
        loader_cls=TextLoader,  # Use TextLoader for .md files
        show_progress=True,
        use_multithreading=True
    )
    md_documents = loader.load()
    
    # Load PDF files separately
    pdf_loader = DirectoryLoader(
        DATA_PATH,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
        use_multithreading=True
    )
    pdf_documents = pdf_loader.load()
    
    # Combine all documents
    all_documents = md_documents + pdf_documents
    print(f"Loaded {len(md_documents)} MD files and {len(pdf_documents)} PDF files")
    return all_documents

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks: list[Document]):
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Use Ollama embeddings
    embedding_function = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    db = Chroma.from_documents(
        chunks, 
        embedding_function, 
        persist_directory=CHROMA_PATH
    )
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

if __name__ == "__main__":
    main()

