import json
import re

# Complete reaction list as a string
REACTIONS_RAW = """HCl + NaOH -> NaCl + H2O
H2SO4 + 2NaOH -> Na2SO4 + 2H2O
HNO3 + KOH -> KNO3 + H2O
CH3COOH + NaOH -> CH3COONa + H2O
HCl + NH3 -> NH4Cl
H2SO4 + 2NH3 -> (NH4)2SO4
HCl + CaCO3 -> CaCl2 + CO2 + H2O
H2SO4 + CaCO3 -> CaSO4 + CO2 + H2O
2HCl + Na2CO3 -> 2NaCl + CO2 + H2O
HNO3 + Ca(OH)2 -> Ca(NO3)2 + 2H2O
AgNO3 + NaCl -> AgCl + NaNO3
AgNO3 + KCl -> AgCl + KNO3
Pb(NO3)2 + 2KI -> PbI2 + 2KNO3
BaCl2 + Na2SO4 -> BaSO4 + 2NaCl
CaCl2 + Na2CO3 -> CaCO3 + 2NaCl
CuSO4 + 2NaOH -> Cu(OH)2 + Na2SO4
FeCl3 + 3NaOH -> Fe(OH)3 + 3NaCl
ZnSO4 + 2NaOH -> Zn(OH)2 + Na2SO4
AlCl3 + 3NaOH -> Al(OH)3 + 3NaCl
MgCl2 + 2NaOH -> Mg(OH)2 + 2NaCl
Zn + 2HCl -> ZnCl2 + H2
Mg + 2HCl -> MgCl2 + H2
Fe + H2SO4 -> FeSO4 + H2
2Al + 6HCl -> 2AlCl3 + 3H2
Cu + 4HNO3 -> Cu(NO3)2 + 2NO2 + 2H2O
3Cu + 8HNO3 -> 3Cu(NO3)2 + 2NO + 4H2O
Zn + CuSO4 -> ZnSO4 + Cu
Fe + CuSO4 -> FeSO4 + Cu
Mg + CuSO4 -> MgSO4 + Cu
2Al + 3CuSO4 -> Al2(SO4)3 + 3Cu
CH4 + 2O2 -> CO2 + 2H2O
2C2H6 + 7O2 -> 4CO2 + 6H2O
C3H8 + 5O2 -> 3CO2 + 4H2O
2C4H10 + 13O2 -> 8CO2 + 10H2O
C6H12O6 + 6O2 -> 6CO2 + 6H2O
2Mg + O2 -> 2MgO
4Al + 3O2 -> 2Al2O3
4Fe + 3O2 -> 2Fe2O3
S + O2 -> SO2
2H2 + O2 -> 2H2O
2H2O2 -> 2H2O + O2
CaCO3 -> CaO + CO2
2KClO3 -> 2KCl + 3O2
2HgO -> 2Hg + O2
2NaHCO3 -> Na2CO3 + H2O + CO2
NH4Cl -> NH3 + HCl
(NH4)2CO3 -> 2NH3 + H2O + CO2
CuCO3 -> CuO + CO2
2Ag2O -> 4Ag + O2
2Pb(NO3)2 -> 2PbO + 4NO2 + O2
Cl2 + 2NaBr -> 2NaCl + Br2
Br2 + 2KI -> 2KBr + I2
F2 + 2NaCl -> 2NaF + Cl2
Mg + 2AgNO3 -> Mg(NO3)2 + 2Ag
Zn + 2AgNO3 -> Zn(NO3)2 + 2Ag
Fe + 2AgNO3 -> Fe(NO3)2 + 2Ag
Cu + 2AgNO3 -> Cu(NO3)2 + 2Ag
Cl2 + 2KBr -> 2KCl + Br2
Br2 + 2NaI -> 2NaBr + I2
Mg + FeSO4 -> MgSO4 + Fe
CH4 + 2O2 -> CO2 + 2H2O
C2H6 + 3.5O2 -> 2CO2 + 3H2O
C3H8 + 5O2 -> 3CO2 + 4H2O
C4H10 + 6.5O2 -> 4CO2 + 5H2O
C6H6 + 7.5O2 -> 6CO2 + 3H2O
CH3OH + 1.5O2 -> CO2 + 2H2O
C2H5OH + 3O2 -> 2CO2 + 3H2O
CH3CHO + 2.5O2 -> 2CO2 + 2H2O
CH3COOH + 2O2 -> 2CO2 + 2H2O
C12H22O11 + 12O2 -> 12CO2 + 11H2O
CH4 + Cl2 -> CH3Cl + HCl
CH3Cl + Cl2 -> CH2Cl2 + HCl
CH2Cl2 + Cl2 -> CHCl3 + HCl
CHCl3 + Cl2 -> CCl4 + HCl
C2H6 + Cl2 -> C2H5Cl + HCl
C6H6 + Br2 -> C6H5Br + HBr
C2H5OH + HBr -> C2H5Br + H2O
CH3COOH + CH3OH -> CH3COOCH3 + H2O
C6H5OH + NaOH -> C6H5ONa + H2O
CH3Cl + NaOH -> CH3OH + NaCl
C2H4 + H2 -> C2H6
C2H2 + H2 -> C2H4
C3H6 + H2 -> C3H8
C2H4 + Br2 -> C2H4Br2
C2H2 + Br2 -> C2H2Br2
C2H2 + 2Br2 -> C2H2Br4
C2H4 + HCl -> C2H5Cl
C3H6 + HCl -> C3H7Cl
C2H2 + HCl -> CH2CHCl
C2H4 + H2O -> C2H5OH
C2H5OH -> C2H4 + H2O
C3H7OH -> C3H6 + H2O
CH3CHClCH3 -> CH3CHCH2 + HCl
C2H5Br -> C2H4 + HBr
(CH3)3COH -> (CH3)2CCH2 + H2O
CH3CH2CH2Br -> CH3CHCH2 + HBr
C2H5OH + H2SO4 -> C2H4 + H2O
CH3CH2CH2OH -> CH3CHCH2 + H2O
(CH3)2CHBr -> (CH3)2CCH2 + HBr
C4H9OH -> C4H8 + H2O
CH3CH2OH -> CH3CHO
CH3CHO -> CH3COOH
C2H5OH + O2 -> CH3COOH + H2O
CH3CH2CH2OH -> CH3CH2CHO
CH3CH2CHO -> CH3CH2COOH
C6H5CH3 -> C6H5COOH
CH3CHOHCH3 -> CH3COCH3
CH3CH2CH2OH -> CH3CH2COOH
HCHO -> HCOOH
CH3CH2OH -> CH3COOH
CH3COOH + C2H5OH -> CH3COOC2H5 + H2O
HCOOH + CH3OH -> HCOOCH3 + H2O
CH3CH2COOH + CH3OH -> CH3CH2COOCH3 + H2O
C6H5COOH + CH3OH -> C6H5COOCH3 + H2O
CH3COOH + CH3CH2CH2OH -> CH3COOCH2CH2CH3 + H2O
HCOOH + C2H5OH -> HCOOC2H5 + H2O
CH3CH2COOH + C2H5OH -> CH3CH2COOC2H5 + H2O
C6H5COOH + C2H5OH -> C6H5COOC2H5 + H2O
CH3COOH + CH3CH2CH2CH2OH -> CH3COOC4H9 + H2O
HCOOH + CH3CH2CH2OH -> HCOOC3H7 + H2O
N2 + 3H2 -> 2NH3
2SO2 + O2 -> 2SO3
SO3 + H2O -> H2SO4
CaO + SiO2 -> CaSiO3
2Al2O3 -> 4Al + 3O2
2NaCl + 2H2O -> 2NaOH + H2 + Cl2
CH4 + H2O -> CO + 3H2
CO + H2O -> CO2 + H2
C6H6 + HNO3 -> C6H5NO2 + H2O
C6H6 + CH3Cl -> C6H5CH3 + HCl
2AgBr -> 2Ag + Br2
2AgCl -> 2Ag + Cl2
2HI -> H2 + I2
2H2O2 -> 2H2O + O2
CO2 + H2O -> CH2O + O2
2O3 -> 3O2
NO2 -> NO + O
Cl2 + H2 -> 2HCl
2NO2 -> 2NO + O2
CH3COCH3 -> C2H6 + CO
2H2O -> 2H2 + O2
2NaCl + 2H2O -> 2NaOH + H2 + Cl2
CuSO4 + Zn -> ZnSO4 + Cu
2AgNO3 + Cu -> Cu(NO3)2 + 2Ag
Pb + PbO2 + 2H2SO4 -> 2PbSO4 + 2H2O
Zn + 2MnO2 + 2NH4Cl -> ZnCl2 + Mn2O3 + 2NH3 + H2O
2Al + Cr2O3 -> Al2O3 + 2Cr
Mg + 2AgNO3 -> Mg(NO3)2 + 2Ag
Fe + NiSO4 -> FeSO4 + Ni
2K + 2H2O -> 2KOH + H2
2NaOH + Cl2 -> NaCl + NaClO + H2O
2FeCl3 + 2KI -> 2FeCl2 + I2 + 2KCl
K2Cr2O7 + H2SO4 + 3SO2 -> K2SO4 + Cr2(SO4)3 + H2O
2KMnO4 + 5H2C2O4 + 3H2SO4 -> K2SO4 + 2MnSO4 + 10CO2 + 8H2O
I2 + 2Na2S2O3 -> 2NaI + Na2S4O6
CuSO4 + 4NH3 -> [Cu(NH3)4]SO4
FeCl3 + KSCN -> Fe(SCN)3 + 3KCl
CoCl2 + 6H2O -> CoCl2·6H2O
NiSO4 + 6NH3 -> [Ni(NH3)6]SO4
CrCl3 + 6H2O -> [Cr(H2O)6]Cl3
CaCO3 + 2HCl -> CaCl2 + CO2 + H2O
Na2CO3 + 2HCl -> 2NaCl + CO2 + H2O
NaHCO3 + HCl -> NaCl + CO2 + H2O
FeS + 2HCl -> FeCl2 + H2S
ZnS + 2HCl -> ZnCl2 + H2S
Na2S + 2HCl -> 2NaCl + H2S
NH4Cl + NaOH -> NaCl + NH3 + H2O
(NH4)2SO4 + 2NaOH -> Na2SO4 + 2NH3 + 2H2O
2H2O2 -> 2H2O + O2
2Na + 2H2O -> 2NaOH + H2
Ca + 2H2O -> Ca(OH)2 + H2
2K + 2H2O -> 2KOH + H2
Ba + 2H2O -> Ba(OH)2 + H2
2Na + Cl2 -> 2NaCl
2K + Cl2 -> 2KCl
Mg + Cl2 -> MgCl2
Ca + Cl2 -> CaCl2
2Fe + 3Cl2 -> 2FeCl3
2Cu + O2 -> 2CuO
4Na + O2 -> 2Na2O
4K + O2 -> 2K2O
2Ca + O2 -> 2CaO
2Ba + O2 -> 2BaO
2Zn + O2 -> 2ZnO
4Li + O2 -> 2Li2O
CH3COCl + H2O -> CH3COOH + HCl
PCl5 + H2O -> POCl3 + 2HCl
PCl3 + 3H2O -> H3PO3 + 3HCl
SiCl4 + 2H2O -> SiO2 + 4HCl
AlCl3 + 3H2O -> Al(OH)3 + 3HCl
CaC2 + 2H2O -> Ca(OH)2 + C2H2
Mg3N2 + 6H2O -> 3Mg(OH)2 + 2NH3
Al4C3 + 12H2O -> 4Al(OH)3 + 3CH4
NaH + H2O -> NaOH + H2
CaH2 + 2H2O -> Ca(OH)2 + 2H2
LiAlH4 + 4H2O -> LiOH + Al(OH)3 + 4H2
SO2Cl2 + 2H2O -> H2SO4 + 2HCl
COCl2 + H2O -> CO2 + 2HCl
NOCl + H2O -> HNO2 + HCl
SO3 + H2O -> H2SO4"""

def parse_chemical_formula(formula):
    """Parse chemical formula to get base components"""
    formula = formula.strip()
    # Remove coefficients and state symbols
    formula = re.sub(r'^\d+', '', formula)  # Remove leading coefficients (e.g., "2H2O" -> "H2O")
    formula = re.sub(r'\([a-z]+\)$', '', formula)  # Remove state symbols like (g), (l), (s), (aq)
    return formula.strip()

def determine_must_not_contain(reactants_str, products_list):
    """Determine what should not be in products"""
    reactants = [parse_chemical_formula(r) for r in reactants_str.split('+')]
    must_not_contain = []
    
    for reactant in reactants:
        reactant_clean = reactant.strip()
        # Don't include simple elements that might be part of products (like O from O2)
        if len(reactant_clean) <= 2 or reactant_clean in ["O2", "H2", "N2", "Cl2", "Br2", "I2", "F2"]:
            # For diatomic elements, check if they appear in products as elements
            element = reactant_clean.rstrip('2') if reactant_clean.endswith('2') else reactant_clean
            if not any(element in p for p in products_list):
                must_not_contain.append(reactant_clean)
        else:
            # For compounds, check if they appear unchanged
            if not any(reactant_clean in p for p in products_list):
                must_not_contain.append(reactant_clean)
    
    return list(set(must_not_contain))

def get_category(reaction):
    """Categorize the reaction type"""
    reactants = reaction.split('->')[0]
    
    if 'O2' in reactants and '->' in reaction:
        products = reaction.split('->')[1]
        if 'CO2' in products and 'H2O' in products:
            return "combustion"
    
    if 'HCl' in reactants or 'H2SO4' in reactants or 'NaOH' in reactants:
        if 'H2O' in reaction:
            return "acid-base"
    
    if 'AgNO3' in reactants or 'Pb(NO3)2' in reactants:
        return "precipitation"
    
    if any(metal in reactants for metal in ['Zn', 'Mg', 'Fe', 'Al']) and ('HCl' in reactants or 'H2SO4' in reactants):
        return "redox"
    
    if '->' in reaction and reaction.count('->') == 1 and '+' not in reaction.split('->')[0]:
        return "decomposition"
    
    if any(x in reactants for x in ['Cl2', 'Br2', 'I2', 'F2']):
        return "halogenation"
    
    return "general"

def parse_reaction_to_json(reaction_str, index, temperature=25.0):
    """Parse a single reaction string to JSON format"""
    try:
        # Split reaction
        if '->' in reaction_str:
            reactants_part, products_part = reaction_str.split('->')
        else:
            # Try with = if -> not present
            reactants_part, products_part = reaction_str.split('=')
        
        # Clean up
        reactants_part = reactants_part.strip()
        products_part = products_part.strip()
        
        # Parse products and remove coefficients
        products = [parse_chemical_formula(p) for p in products_part.split('+')]
        
        # Get reactants without coefficients for must_not_contain
        reactants_list = [parse_chemical_formula(r) for r in reactants_part.split('+')]
        
        # Determine must_not_contain
        must_not_contain = determine_must_not_contain(reactants_part, products)
        
        # Get category
        category = get_category(reaction_str)
        
        # Determine conditions based on category
        conditions_map = {
            "combustion": "combustion",
            "acid-base": "aqueous solution",
            "precipitation": "aqueous solution",
            "redox": "aqueous solution",
            "decomposition": "thermal decomposition",
            "halogenation": "light or heat",
            "general": "standard conditions"
        }
        conditions = conditions_map.get(category, "standard conditions")
        
        # Create test case
        test_case = {
            "reactants": reactants_part,
            "conditions": conditions,
            "temperature": temperature,
            "expected": {
                "products": products,
                "must_contain": products.copy(),  # All products should be contained
                "must_not_contain": must_not_contain,
                "equation": reaction_str#.replace('->', '->')
            },
            "category": category,
            "id": index + 1
        }
        
        return test_case
        
    except Exception as e:
        print(f"Error parsing reaction {index + 1}: {reaction_str}")
        print(f"Error: {e}")
        return None

def create_test_dataset():
    """Create complete test dataset"""
    reactions = REACTIONS_RAW.split('\n')
    test_cases = []
    
    for i, reaction in enumerate(reactions):
        if reaction.strip():  # Skip empty lines
            test_case = parse_reaction_to_json(reaction, i)
            if test_case:
                test_cases.append(test_case)
    
    return test_cases

def save_to_json(test_cases, filename="tests/data/products_test_data.json"):
    """Save test cases to JSON file"""
    with open(filename, 'w') as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"Saved {len(test_cases)} test cases to {filename}")
    
    # Print summary
    categories = {}
    for case in test_cases:
        cat = case.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory summary:")
    for cat, count in categories.items():
        print(f"  {cat}: {count} reactions")

if __name__ == "__main__":
    # Create test dataset
    test_dataset = create_test_dataset()
    
    # Save to JSON
    save_to_json(test_dataset)
    
    # Also save a smaller subset for quick testing
    small_subset = test_dataset[:50]  # First 50 reactions
    save_to_json(small_subset, "tests/data/chemical_reactions_small_test_dataset.json")
    
    # Print a few examples
    print("\nSample test cases:")
    for i in range(min(3, len(test_dataset))):
        print(f"\nExample {i + 1}:")
        print(json.dumps(test_dataset[i], indent=2))