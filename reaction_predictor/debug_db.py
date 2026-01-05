# debug_database.py
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "chroma"

def debug_database():
    # Use the same embeddings as your query
    embedding_function = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Check if database has any documents
    print("=== DATABASE DEBUG INFO ===")
    print(f"Persist directory: {CHROMA_PATH}")
    
    # Get collection count
    collection = db._collection
    count = collection.count()
    print(f"Number of documents in database: {count}")
    
    if count == 0:
        print("❌ Database is EMPTY! Check your data creation process.")
        return
    
    # Try a simple search without threshold
    print("\n=== TESTING SIMILARITY SEARCH ===")
    test_queries = ["book", "story", "character", "the", "and"]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        try:
            # Test without relevance scores first
            results = db.similarity_search(query, k=3)
            print(f"Found {len(results)} results")
            
            # Test with relevance scores
            results_with_scores = db.similarity_search_with_relevance_scores(query, k=3)
            print(f"Relevance scores: {[score for _, score in results_with_scores]}")
            
            if results:
                print("Sample document content:")
                print(results[0].page_content[:200] + "...")
                
        except Exception as e:
            print(f"Error with query '{query}': {e}")
    
    # List all documents (first few)
    print("\n=== SAMPLE DOCUMENTS ===")
    all_docs = db.get()  # This gets all documents
    if all_docs and 'documents' in all_docs:
        for i, doc in enumerate(all_docs['documents'][:3]):  # Show first 3
            print(f"Document {i}: {doc[:100]}...")

if __name__ == "__main__":
    debug_database()