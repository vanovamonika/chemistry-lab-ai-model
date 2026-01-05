import dotenv
import requests
import PyPDF2
import os
from bs4 import BeautifulSoup
import time

DATA_PATH = dotenv.get_key(dotenv.find_dotenv(), "DATA_PATH") or "data"

def download_openstax_chemistry():
    """Download OpenStax Chemistry textbook"""
    urls = {
        # 1. Comprehensive Foundation
        'general_chemistry': 'https://assets.openstax.org/oscms-prodcms/media/documents/Chemistry2e-WEB.pdf',
        }
    
    for name, url in urls.items():
        print(f"Downloading {name}...")
        response = requests.get(url)
        with open(DATA_PATH + f"/{name}.pdf", 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {name}")

def extract_inorganic_sections(pdf_path, output_path):
    """Extract inorganic chemistry relevant sections from PDF"""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        inorganic_keywords = [
            'reaction', 'redox', 'oxidation', 'reduction', 'acid', 'base',
            'precipitation', 'complex', 'coordination', 'transition metal',
            'solubility', 'displacement', 'decomposition', 'synthesis',
            'combustion', 'neutralization', 'electrochemistry'
        ]
        
        content = ""
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            
            # Check if page contains inorganic chemistry content
            if any(keyword in text.lower() for keyword in inorganic_keywords):
                content += f"\n\n--- Page {page_num} ---\n\n"
                content += text
        
        # Save extracted content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Extracted {len(content)} characters to {output_path}")

def scrape_libretexts_inorganic():
    """Scrape inorganic chemistry content from LibreTexts"""
    base_url = "https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry"
    
    # Key inorganic chemistry pages
    pages = [
        "/Map%3A_Inorganic_Chemistry_(Housecroft)",
        "/Supplemental_Modules_(Inorganic_Chemistry)",
        "/Descriptive_Chemistry",
        "/Coordination_Chemistry"
    ]
    
    for page in pages:
        url = base_url + page
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content = soup.get_text()
            
            # Save to file
            filename = DATA_PATH + f"/libretexts_{page.split('/')[-1]}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Saved {filename}")
            time.sleep(1)  # Be respectful to the server
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")

def create_comprehensive_reaction_database():
    """Create a comprehensive reaction database from multiple sources"""
    reaction_data = """
# Comprehensive Inorganic Reaction Database

## 1. SOLUBILITY RULES (COMPLETE)
### Always Soluble
- Group 1 (Li⁺, Na⁺, K⁺, Rb⁺, Cs⁺) salts
- Ammonium (NH₄⁺) salts  
- Nitrates (NO₃⁻)
- Acetates (CH₃COO⁻)
- Chlorates (ClO₃⁻)
- Perchlorates (ClO₄⁻)

### Mostly Soluble
- Chlorides (Cl⁻), Bromides (Br⁻), Iodides (I⁻)
  * EXCEPTIONS: Ag⁺, Pb²⁺, Hg₂²⁺
- Sulfates (SO₄²⁻)
  * EXCEPTIONS: Ba²⁺, Sr²⁺, Pb²⁺, Ca²⁺ (slightly), Hg⁺, Ag⁺

### Mostly Insoluble
- Hydroxides (OH⁻)
  * EXCEPTIONS: Group 1, Ba²⁺, Sr²⁺, Ca²⁺ (slightly)
- Carbonates (CO₃²⁻), Phosphates (PO₄³⁻), Sulfides (S²⁻)
  * EXCEPTIONS: Group 1, NH₄⁺

## 2. REDOX REACTION PATTERNS

### Activity Series (Strongest Reducing Agents First)
- Li > K > Ba > Sr > Ca > Na > Mg > Al > Mn > Zn > Cr > Fe > Cd > Co > Ni > Sn > Pb > H > Cu > Ag > Hg > Pt > Au

### Common Oxidizing Agents
- MnO₄⁻ (acidic): MnO₄⁻ + 8H⁺ + 5e⁻ → Mn²⁺ + 4H₂O
- Cr₂O₇²⁻: Cr₂O₇²⁻ + 14H⁺ + 6e⁻ → 2Cr³⁺ + 7H₂O  
- HNO₃ (conc): NO₃⁻ + 2H⁺ + e⁻ → NO₂ + H₂O
- HNO₃ (dil): NO₃⁻ + 4H⁺ + 3e⁻ → NO + 2H₂O
- H₂O₂: H₂O₂ + 2H⁺ + 2e⁻ → 2H₂O
- Cl₂: Cl₂ + 2e⁻ → 2Cl⁻
- O₂: O₂ + 4H⁺ + 4e⁻ → 2H₂O

### Common Reducing Agents
- Metals: M → Mⁿ⁺ + ne⁻
- I⁻: 2I⁻ → I₂ + 2e⁻
- Fe²⁺: Fe²⁺ → Fe³⁺ + e⁻
- SO₃²⁻: SO₃²⁻ + H₂O → SO₄²⁻ + 2H⁺ + 2e⁻
- C₂O₄²⁻: C₂O₄²⁻ → 2CO₂ + 2e⁻

## 3. ACID-BASE REACTION PATTERNS

### Strong Acids
- HCl, HBr, HI, HNO₃, H₂SO₄, HClO₄, HClO₃

### Strong Bases
- Group 1 hydroxides: LiOH, NaOH, KOH, RbOH, CsOH
- Heavy Group 2 hydroxides: Ca(OH)₂, Sr(OH)₂, Ba(OH)₂

### Weak Acids
- HF, CH₃COOH, H₂CO₃, H₃PO₄, H₂S, HCN, HNO₂

### Weak Bases
- NH₃, amines, HCO₃⁻, CO₃²⁻, PO₄³⁻

### Acid-Base Reaction Types
1. Strong acid + strong base → salt + water (neutral)
2. Strong acid + weak base → salt + acidic solution
3. Weak acid + strong base → salt + basic solution  
4. Weak acid + weak base → depends on relative strengths
5. Metal oxide + acid → salt + water
6. Nonmetal oxide + base → salt + water
7. Carbonate/hydrogen carbonate + acid → CO₂ + salt + water

## 4. COMPLEXATION REACTIONS

### Common Ligands (increasing field strength)
I⁻ < Br⁻ < Cl⁻ < F⁻ < OH⁻ < H₂O < NH₃ < CN⁻ < CO

### Coordination Numbers & Geometries
- 2: Linear (Ag⁺, Cu⁺, Au⁺)
- 4: Tetrahedral (Zn²⁺, Cd²⁺, Hg²⁺) or Square planar (Ni²⁺, Pt²⁺, Pd²⁺)
- 6: Octahedral (most transition metals)

### Common Complex Ions
- [Ag(NH₃)₂]⁺, [Cu(NH₃)₄]²⁺, [Fe(CN)₆]⁴⁻, [Fe(CN)₆]³⁻
- [Ag(CN)₂]⁻, [Zn(OH)₄]²⁻, [Al(OH)₄]⁻, [CuCl₄]²⁻

## 5. PRECIPITATION REACTIONS

### Prediction Algorithm
1. Identify all ions present
2. Exchange cations and anions
3. Apply solubility rules to possible products
4. If any product is insoluble, precipitation occurs

### Common Precipitates
- AgCl, AgBr, AgI (colored)
- PbCl₂, PbBr₂, PbI₂ (yellow)
- BaSO₄, PbSO₄, SrSO₄ (white)
- CaCO₃, BaCO₃, MgCO₃ (white)
- Fe(OH)₃ (rust brown), Cu(OH)₂ (blue), Zn(OH)₂ (white)

## 6. GAS-FORMING REACTIONS

### Patterns
- Acid + carbonate → CO₂ + salt + water
- Acid + sulfite → SO₂ + salt + water  
- Acid + sulfide → H₂S + salt
- Ammonium salt + strong base → NH₃ + salt + water
- Active metal + acid → H₂ + salt

## 7. DECOMPOSITION REACTIONS

### Thermal Decomposition Patterns
- Carbonates: MCO₃ → MO + CO₂ (stability: Group 1 > Group 2 > transition)
- Hydroxides: M(OH)₂ → MO + H₂O
- Nitrates:
  * Group 1: 2MNO₃ → 2MNO₂ + O₂ (except Li)
  * Others: 2M(NO₃)₂ → 2MO + 4NO₂ + O₂
- Chlorates: 2MClO₃ → 2MCl + 3O₂

## 8. DISPROPORTIONATION REACTIONS

### Common Examples
- Cl₂ + H₂O → HCl + HOCl
- 2Cu⁺ → Cu + Cu²⁺
- 3MnO₄²⁻ + 2H₂O → 2MnO₄⁻ + MnO₂ + 4OH⁻
- 2H₂O₂ → 2H₂O + O₂ (catalyzed)

## REACTION PREDICTION FLOWCHART

1. **Identify Reactants**
   - Metal + acid? → Redox (H₂ gas)
   - Metal + salt? → Single displacement
   - Two salts in solution? → Precipitation check
   - Acid + base? → Neutralization
   - Transition metal + ligand? → Complexation
   - Carbonate + acid? → Gas formation

2. **Check Solubility** (use rules above)

3. **Assign Oxidation Numbers** for redox potential

4. **Consider Complex Formation** with excess ligands

5. **Apply Thermal Stability Rules** for decomposition

6. **Predict Products** based on driving forces
"""

    with open(DATA_PATH + "/comprehensive_reaction_database.md", "w", encoding="utf-8") as f:
        f.write(reaction_data)
    
    print("Created comprehensive reaction database")

if __name__ == "__main__":
    # Create directories
    os.makedirs(DATA_PATH, exist_ok=True)
    
    # Download and process resources
    download_openstax_chemistry()
    scrape_libretexts_inorganic()
    create_comprehensive_reaction_database()
    
    # Process downloaded PDFs
    for pdf_file in os.listdir(DATA_PATH):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(DATA_PATH, pdf_file)
            output_path = os.path.join(DATA_PATH, pdf_file.replace(".pdf", "_extracted.txt"))
            extract_inorganic_sections(pdf_path, output_path)