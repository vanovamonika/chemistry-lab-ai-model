import requests
import re

common_chemicals = {
    "H₂O": "water",
    "H2O": "water",
    "O": "water",
}

def get_smile_reaction_formula_from_names(formula: str):
    single_reactants = formula.split('+')
    print(single_reactants)
    smiles = ""
    for reactant in single_reactants:
        
        smile = chemical_name_to_smiles(reactant)
        print("converting reactant: " + reactant + " to  smiles " + smile)
        smiles += smile
        if reactant != single_reactants[-1]:
            smiles += "."
    return smiles

def chemical_name_to_smiles(chemical_name):
    """
    Convert chemical name to SMILES using PubChem API
    """
    try:
        # Convert to PubChem Compound ID (CID) first
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{chemical_name}/cids/JSON"
        response = requests.get(url)
        cid = response.json()['IdentifierList']['CID'][0]
        
        # Get SMILES from CID
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES/JSON"
        response = requests.get(url)
        smiles = response.json()['PropertyTable']['Properties'][0]['ConnectivitySMILES']
        
        return smiles
    except Exception as e:
        print(f"Error converting {chemical_name}: {e}")
        return None

def smiles_to_chemical_name(smiles: str):
    """
    Convert SMILES string to chemical name using PubChem API
    """
    if not smiles or smiles.strip() == "":
        return None
        
    smiles = clean_smiles(smiles)
    if smiles in common_chemicals:
        return common_chemicals[smiles]
    
    try:
        # print(f"Converting SMILES to name: {smiles}")
        
        # Convert SMILES to PubChem Compound ID (CID)
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/cids/JSON"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"PubChem API error for SMILES {smiles}: Status {response.status_code}")
            return None
            
        data = response.json()
        
        if 'IdentifierList' not in data or 'CID' not in data['IdentifierList']:
            print(f"No CID found for SMILES {smiles}")
            return None
            
        cids = data['IdentifierList']['CID']
        if not cids:
            print(f"No compounds found for SMILES {smiles}")
            return None
            
        cid = cids[0]
        
        # Get chemical name from CID
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IUPACName,Title/JSON"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"PubChem API error for CID {cid}: Status {response.status_code}")
            return None
            
        data = response.json()
        
        if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
            properties = data['PropertyTable']['Properties'][0]
            
            # Prefer IUPAC name, fallback to Title
            if 'IUPACName' in properties and properties['IUPACName']:
                name = properties['IUPACName']
            elif 'Title' in properties and properties['Title']:
                name = properties['Title']
            else:
                print(f"No name found for SMILES {smiles}")
                return None
                
            # print(f"Successfully converted SMILES '{smiles}' to name: {name}")
            return name
        else:
            print(f"No properties found for SMILES {smiles}")
            return None
            
    except Exception as e:
        print(f"Error converting SMILES {smiles}: {e}")
        return None

def get_name_reaction_formula_from_smiles(smiles_formula: str):
    """
    Convert SMILES reaction formula to names
    Example: "CCO.CC(=O)O" -> "ethanol + acetic acid"
    """
    single_reactants = smiles_formula.split('.')
    names = []
    for smiles in single_reactants:
        name = smiles_to_chemical_name(smiles.strip())
        if name:
            names.append(name)
        else:
            names.append(smiles)  # Fallback to SMILES if name not found
    
    return " + ".join(names)

def clean_smiles(smiles: str) -> str:
    """
    Clean SMILES strings for consistent formatting
    """
    if not smiles:
        return ""
    
    # Remove spaces and standardize
    cleaned = smiles.replace(' ', '').replace('\n', '').strip()
    
    # Fix common ion representations
    cleaned = re.sub(r'\[(\w+)\s*\+\s*\]', r'[\1+]', cleaned)  # [Na +] -> [Na+]
    cleaned = re.sub(r'\[(\w+)\s*\-\s*\]', r'[\1-]', cleaned)  # [OH -] -> [OH-]
    
    return cleaned

def is_likely_smiles(input_str: str) -> bool:
    """
    Check if input looks like a SMILES string
    """
    smiles_patterns = ['=', '(', ')', '[', ']', '@', '+', '-', '#', '%', '\\']
    return any(pattern in input_str for pattern in smiles_patterns)

def batch_smiles_to_names(smiles_list: list):
    """
    Convert multiple SMILES strings to names
    """
    results = {}
    for smiles in smiles_list:
        name = smiles_to_chemical_name(smiles)
        results[smiles] = name
    return results

def batch_names_to_smiles(names_list: list):
    """
    Convert multiple chemical names to SMILES
    """
    results = {}
    for name in names_list:
        smiles = chemical_name_to_smiles(name)
        results[name] = smiles
    return results

# Test functions
def test_conversions():
    """Test both name-to-SMILES and SMILES-to-name conversions"""
    test_cases = [
        "benzene",
        "ethanol", 
        "acetic acid",
        "aspirin"
    ]
    
    print("Testing Name -> SMILES -> Name conversion")
    print("=" * 50)
    
    for name in test_cases:
        print(f"\nOriginal name: {name}")
        
        # Name to SMILES
        smiles = chemical_name_to_smiles(name)
        if smiles:
            print(f"SMILES: {smiles}")
            
            # SMILES back to name
            recovered_name = smiles_to_chemical_name(smiles)
            print(f"Recovered name: {recovered_name}")
        else:
            print(f"Failed to convert {name} to SMILES")
        
        print("-" * 30)

def test_reaction_conversions():
    """Test reaction formula conversions"""
    print("\nTesting Reaction Formula Conversions")
    print("=" * 50)
    
    # Name reaction formula to SMILES
    name_formula = "ethanol+acetic acid"
    smiles_formula = get_smile_reaction_formula_from_names(name_formula)
    print(f"Name formula: {name_formula}")
    print(f"SMILES formula: {smiles_formula}")
    
    # SMILES reaction formula back to names
    if smiles_formula:
        recovered_names = get_name_reaction_formula_from_smiles(smiles_formula)
        print(f"Recovered names: {recovered_names}")

# Examples
# if __name__ == "__main__":
#     # Test individual conversions
#     test_conversions()
    
#     # Test reaction conversions
#     test_reaction_conversions()
    
#     # Individual examples
#     print("\nIndividual Examples:")
#     print("=" * 30)
    
#     # Name to SMILES
#     benzene_smiles = chemical_name_to_smiles("benzene")
#     print(f"benzene -> {benzene_smiles}")
    
#     ethanol_smiles = chemical_name_to_smiles("ethanol")
#     print(f"ethanol -> {ethanol_smiles}")
    
#     # SMILES to name
#     benzene_name = smiles_to_chemical_name("c1ccccc1")
#     print(f"c1ccccc1 -> {benzene_name}")
    
#     ethanol_name = smiles_to_chemical_name("CCO")
#     print(f"CCO -> {ethanol_name}")
    
#     # Reaction formulas
#     reaction_smiles = get_smile_reaction_formula_from_names("ethanol+acetic acid")
#     print(f"ethanol+acetic acid -> {reaction_smiles}")
    
#     if reaction_smiles:
#         reaction_names = get_name_reaction_formula_from_smiles(reaction_smiles)
#         print(f"{reaction_smiles} -> {reaction_names}")


