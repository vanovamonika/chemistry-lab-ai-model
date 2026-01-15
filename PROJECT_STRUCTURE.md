# Project Structure

## Directory Tree

```
langchain-rag-tutorial-main/
├── main.py
├── README.md
├── requirements.txt
├── .env
├── .vscode/
│   └── settings.json
│
├── chroma/
│   ├── chroma.sqlite3
│   └── fbc338bc-dd21-49d0-ac6d-5d3af21582b3/
│       ├── data_level0.bin
│       ├── header.bin
│       ├── length.bin
│       └── link_lists.bin
│
├── data/
│   ├── 4-inorganic-chemistry.pdf
│   ├── A Guidebook of Organic Reaction Mechanism by Peter Sykes.pdf
│   ├── ATOICV1-3-0-Reaction-Mechanism-of-Transition-Metal-Complexes-I.pdf
│   ├── Basic Inorganic Chemistry-F. Albert Cotton, Geoffrey Wilkinson, Paul L. Gaus - 3rd Edition-Wiley (1994).pdf
│   ├── Chemistry_Principles_and_Reactions.pdf
│   ├── comprehensive_reaction_database.md
│   ├── inorganic_reactions.md
│   ├── null-1.pdf
│   ├── organic-reactions.pdf
│   ├── P69-Cws.pdf
│   └── reactions_of_compound_types.md
│
├── prompts/
│   ├── analyze_reactants_prompt copy.md
│   ├── analyze_reactants_prompt.md
│   ├── compound_visual_prediction_prompt.md
│   ├── long_response_prompt.md
│   ├── only_equation_prompt.md
│   ├── only_products_prompt.md
│   ├── process_knowledge.md
│   └── reaction_visual_prediction_prompt.md
│
├── reaction_predictor/
│   ├── __init__.py
│   ├── api_server.py
│   ├── compare_embeddings.py
│   ├── create_database.py
│   ├── debug_db.py
│   ├── dto.py
│   ├── get_sources.py
│   ├── molecular_transformer.py
│   ├── parse_reaction_file.py
│   ├── query_data.py
│   ├── reaction_predictor_class.py
│   ├── smiles_converter.py
│   └── visual_prediction.py
│
└── tests/
    ├── __init__.py
    ├── api_test.py
    ├── reaction_predictor_test.py
    ├── test_smiles_converter.py
    └── data/
        ├── compound_visuals_test_data.json
        ├── inorganic_test_data.json
        ├── no_reaction_test_data.json
        ├── organic_test_data.json
        ├── reaction_test_data.json
        ├── reaction_test_data.txt
        ├── reaction_test_data.txt.json
        ├── reaction_visuals_test_data.json
        ├── reactionSmilesFigShareUSPTO2023.txt
        └── test_data.json
```

## File Descriptions

### Root Level
- **main.py** - Main application entry point
- **README.md** - Project documentation
- **requirements.txt** - Python package dependencies
- **.env** - Environment variables configuration

### chroma/
Vector database storage for embeddings and semantic search data.

### data/
Contains training and reference data:
- **PDF files** - Chemistry textbooks and educational materials
- **Markdown files** - Reaction databases and reference data (comprehensive, inorganic, compound types)

### prompts/
LLM prompt templates for different tasks:
- Reactant analysis
- Product prediction
- Visual reaction prediction
- Compound visual prediction
- Response formatting

### reaction_predictor/
Core module containing reaction prediction logic:
- **api_server.py** - FastAPI server for exposing endpoints
- **reaction_predictor_class.py** - Main prediction class
- **create_database.py** - Database initialization
- **query_data.py** - Data retrieval from vector store
- **smiles_converter.py** - SMILES string conversion utilities
- **molecular_transformer.py** - Molecular embedding generation
- **visual_prediction.py** - Visual/structural predictions
- **compare_embeddings.py** - Embedding comparison logic
- **parse_reaction_file.py** - Reaction file parsing
- **get_sources.py** - Source document retrieval
- **dto.py** - Data transfer objects
- **debug_db.py** - Database debugging utilities

### tests/
Test suite with unit tests and test data:
- **api_test.py** - API endpoint tests
- **reaction_predictor_test.py** - Prediction logic tests
- **test_smiles_converter.py** - SMILES converter tests
- **data/** - Test datasets in JSON and TXT formats
