#!/usr/bin/env python3
"""
Parse chemical reaction file format and convert to JSON.
Format: reactants>reagents>products
"""

import json
import re
import sys
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

def parse_reaction_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a single reaction line in format: reactants>reagents>products
    
    The format is: reactants>reagents>products
    Example: C(=O)(OC(C)(C)C)OC(=O)OC(C)(C)C.NC=1C=CC(=NC1)C(C#N)(C)C>O.O1CCOCC1>C(#N)C(C)(C)C1=CC=C(C=N1)NC(OC(C)(C)C)=O
    
    Returns: Dictionary with 'reactants', 'reagents', 'products' keys
    """
    line = line.strip()
    
    if not line:
        return None
    
    # Split by '>' separator
    parts = line.split('>')
    
    if len(parts) < 2:
        print(f"Warning: Line doesn't have enough '>' separators: {line}")
        return None
    
    # Handle different formats:
    # Format 1: reactants>reagents>products
    if len(parts) == 3:
        reactants = parts[0].strip()
        reagents = parts[1].strip()
        products = parts[2].strip()
    # Format 2: reactants>>products (no reagents)
    elif len(parts) == 2:
        reactants = parts[0].strip()
        reagents = ""
        products = parts[1].strip()
    # More than 3 parts - join middle parts as reagents
    else:
        reactants = parts[0].strip()
        products = parts[-1].strip()
        reagents = ".".join(parts[1:-1])  # Join all middle parts
    
    # Validate that we have at least reactants and products
    if not reactants or not products:
        print(f"Warning: Missing reactants or products in line: {line}")
        return None
    
    return {
        "reactants": reactants,
        "reagents": reagents,
        "products": products,
        "original_line": line
    }

def split_smiles_compounds(smiles_string: str) -> List[str]:
    """
    Split SMILES string into individual compounds.
    Compounds are separated by '.' but we need to be careful with dots inside brackets.
    """
    if not smiles_string:
        return []
    
    compounds = []
    current = ""
    bracket_depth = 0
    square_bracket_depth = 0
    
    for char in smiles_string:
        if char == '(':
            bracket_depth += 1
            current += char
        elif char == ')':
            bracket_depth -= 1
            current += char
        elif char == '[':
            square_bracket_depth += 1
            current += char
        elif char == ']':
            square_bracket_depth -= 1
            current += char
        elif char == '.' and bracket_depth == 0 and square_bracket_depth == 0:
            # Only split on dots that are not inside brackets
            if current:
                compounds.append(current)
                current = ""
        else:
            current += char
    
    # Don't forget the last compound
    if current:
        compounds.append(current)
    
    return compounds

def validate_smiles_compound(smiles: str) -> bool:
    """
    Basic validation of SMILES compound.
    Returns True if the SMILES looks valid.
    """
    if not smiles:
        return False
    
    # Basic SMILES validation rules
    # Must contain at least one letter
    if not re.search(r'[A-Za-z]', smiles):
        return False
    
    # Must have balanced parentheses
    if smiles.count('(') != smiles.count(')'):
        return False
    
    # Must have balanced square brackets
    if smiles.count('[') != smiles.count(']'):
        return False
    
    # Cannot start or end with certain characters
    if smiles.startswith('.') or smiles.endswith('.'):
        return False
    
    return True

def extract_reaction_metadata(reaction_line: str, line_num: int = None) -> Dict[str, any]:
    """
    Extract metadata from a reaction line.
    """
    reaction = parse_reaction_line(reaction_line)
    
    if not reaction:
        return None
    
    # Split into individual compounds
    reactant_compounds = split_smiles_compounds(reaction["reactants"])
    reagent_compounds = split_smiles_compounds(reaction["reagents"])
    product_compounds = split_smiles_compounds(reaction["products"])
    
    # Validate compounds
    valid_reactants = [c for c in reactant_compounds if validate_smiles_compound(c)]
    valid_reagents = [c for c in reagent_compounds if validate_smiles_compound(c)]
    valid_products = [c for c in product_compounds if validate_smiles_compound(c)]
    
    # Count atoms (rough estimate)
    def count_atoms(smiles: str) -> Dict[str, int]:
        """Count atoms in SMILES string"""
        # Remove special characters
        clean = re.sub(r'[0-9\.,=#()\[\]@\+\-\\/]', '', smiles)
        # Count capital letters (usually atoms)
        atoms = re.findall(r'[A-Z][a-z]*', clean)
        from collections import Counter
        return dict(Counter(atoms))
    
    # Combine all atoms in reaction
    all_smiles = reaction["reactants"] + reaction["reagents"] + reaction["products"]
    atom_counts = count_atoms(all_smiles)
    
    # Calculate molecular weights (rough estimate)
    atomic_weights = {
        'C': 12.01, 'H': 1.01, 'O': 16.00, 'N': 14.01,
        'S': 32.06, 'P': 30.97, 'F': 19.00, 'Cl': 35.45,
        'Br': 79.90, 'I': 126.90
    }
    
    total_weight = sum(atomic_weights.get(atom, 12) * count 
                      for atom, count in atom_counts.items())
    
    return {
        "id": f"reaction_{line_num}" if line_num else f"reaction_{hash(reaction_line) % 1000000}",
        "reactants": {
            "smiles": reaction["reactants"],
            "compounds": valid_reactants,
            "count": len(valid_reactants)
        },
        "reagents": {
            "smiles": reaction["reagents"],
            "compounds": valid_reagents,
            "count": len(valid_reagents)
        },
        "products": {
            "smiles": reaction["products"],
            "compounds": valid_products,
            "count": len(valid_products)
        },
        "metadata": {
            "total_atoms": sum(atom_counts.values()),
            "atom_types": atom_counts,
            "estimated_mw": round(total_weight, 2),
            "has_reagents": len(valid_reagents) > 0,
            "reactant_count": len(valid_reactants),
            "product_count": len(valid_products)
        },
        "original_format": reaction["original_line"]
    }

def parse_reaction_file(input_file: str, output_file: str = None, max_lines: int = None) -> List[Dict]:
    """
    Parse a reaction file and convert to JSON format.
    
    Args:
        input_file: Path to input file with reactions
        output_file: Path to output JSON file (optional)
        max_lines: Maximum number of lines to process (optional)
    
    Returns:
        List of parsed reaction dictionaries
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        return []
    
    print(f"Parsing file: {input_file}")
    print(f"File size: {input_path.stat().st_size / 1024:.1f} KB")
    
    reactions = []
    skipped_lines = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            
            # Stop if we've reached max_lines
            if max_lines and len(reactions) >= max_lines:
                print(f"Stopping at {max_lines} reactions as requested")
                break
            
            try:
                reaction_data = extract_reaction_metadata(line, line_num)
                
                if reaction_data:
                    reactions.append(reaction_data)
                    
                    # Progress indicator
                    if line_num % 1000 == 0:
                        print(f"  Processed {line_num} lines, {len(reactions)} reactions parsed")
                else:
                    skipped_lines += 1
                    
            except Exception as e:
                print(f"Error parsing line {line_num}: {e}")
                print(f"  Line: {line[:100]}...")
                skipped_lines += 1
    
    print(f"\nParsing complete!")
    print(f"Total lines processed: {line_num}")
    print(f"Successfully parsed: {len(reactions)} reactions")
    print(f"Skipped/invalid: {skipped_lines} lines")
    
    if reactions:
        # Calculate statistics
        total_reactants = sum(r["reactants"]["count"] for r in reactions)
        total_reagents = sum(r["reagents"]["count"] for r in reactions)
        total_products = sum(r["products"]["count"] for r in reactions)
        reactions_with_reagents = sum(1 for r in reactions if r["reagents"]["count"] > 0)
        
        print(f"\nStatistics:")
        print(f"  Total reactant compounds: {total_reactants}")
        print(f"  Total reagent compounds: {total_reagents}")
        print(f"  Total product compounds: {total_products}")
        print(f"  Reactions with reagents: {reactions_with_reagents} ({reactions_with_reagents/len(reactions)*100:.1f}%)")
        print(f"  Average reactants per reaction: {total_reactants/len(reactions):.2f}")
        print(f"  Average products per reaction: {total_products/len(reactions):.2f}")
        
        # Save to JSON file if output_file specified
        if output_file:
            output_data = {
                "source_file": input_file,
                # "parsing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_reactions": len(reactions),
                "reactions": reactions
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nSaved to: {output_file}")
            print(f"File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
        
        # Also save a simplified version for testing
        if output_file:
            simple_output = output_file.replace('.json', '_simple.json')
            simple_reactions = []
            
            for r in reactions:
                simple_reactions.append({
                    "id": r["id"],
                    "reactants": r["reactants"]["smiles"],
                    "reagents": r["reagents"]["smiles"],
                    "products": r["products"]["smiles"],
                    "reactant_count": r["reactants"]["count"],
                    "product_count": r["products"]["count"]
                })
            
            simple_data = {
                "source_file": input_file,
                "total_reactions": len(simple_reactions),
                "reactions": simple_reactions
            }
            
            with open(simple_output, 'w', encoding='utf-8') as f:
                json.dump(simple_data, f, indent=2, ensure_ascii=False)
            
            print(f"Simplified version saved to: {simple_output}")
    
    return reactions

def convert_to_test_format(reactions: List[Dict], output_file: str) -> None:
    """
    Convert parsed reactions to test format for your model.
    """
    test_cases = []
    
    for i, reaction in enumerate(reactions, 1):
        test_case = {
            "id": f"dataset_{i:06d}",
            "name": f"Dataset Reaction {i}",
            "reactants": reaction["reactants"]["smiles"],
            "reagents": reaction["reagents"]["smiles"],
            "conditions": "standard conditions",
            "temperature": 25.0,
            "reaction_type": "organic",
            "input_format": "smiles",
            "expected": {
                "products": [reaction["products"]["smiles"]],
                "must_contain": reaction["products"]["compounds"],
                "source": "dataset",
                "reactant_count": reaction["reactants"]["count"],
                "product_count": reaction["products"]["count"]
            },
            "metadata": reaction["metadata"],
            "notes": f"From dataset - {reaction['reactants']['count']} reactants, {reaction['products']['count']} products"
        }
        
        # Add specific notes based on reaction characteristics
        if reaction["reagents"]["count"] > 0:
            test_case["notes"] += f", with {reaction['reagents']['count']} reagents"
        
        test_cases.append(test_case)
    
    test_data = {
        "category": "dataset_reactions",
        "description": "Reactions parsed from dataset file",
        "source": "USPTO/ChEMBL dataset",
        "total_tests": len(test_cases),
        "tests": test_cases
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nConverted {len(test_cases)} reactions to test format")
    print(f"Saved to: {output_file}")

def main():
    """Main function for command line usage"""
    import argparse
    # import time
    
    parser = argparse.ArgumentParser(
        description="Parse chemical reaction file and convert to JSON"
    )
    
    parser.add_argument(
        "input_file",
        help="Input file with reactions (format: reactants>reagents>products)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output JSON file (default: input_file.json)"
    )
    
    parser.add_argument(
        "-t", "--test-output",
        default=None,
        help="Output test format JSON file"
    )
    
    parser.add_argument(
        "-m", "--max-lines",
        type=int,
        default=None,
        help="Maximum number of lines to process"
    )
    
    parser.add_argument(
        "-s", "--sample",
        type=int,
        default=0,
        help="Create a sample with N random reactions"
    )
    
    args = parser.parse_args()

    print(f"Input file: {args.input_file}")
    
    # Set default output file if not specified
    if args.output is None:
        args.output = f"{args.input_file}.json"
    
    # Parse the file
    # start_time = time.time()
    reactions = parse_reaction_file(args.input_file, args.output, args.max_lines)
    # parsing_time = time.time() - start_time
    
    # print(f"\nParsing time: {parsing_time:.2f} seconds")
    
    if reactions:
        # Create test format if requested
        if args.test_output:
            convert_to_test_format(reactions, args.test_output)
        
        # Create sample if requested
        if args.sample > 0:
            import random
            sample_size = min(args.sample, len(reactions))
            sample = random.sample(reactions, sample_size)
            
            sample_file = f"{args.input_file}.sample_{sample_size}.json"
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "sample_size": sample_size,
                    "total_reactions": len(reactions),
                    "reactions": sample
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\nCreated sample of {sample_size} reactions in: {sample_file}")
            
            # Also create test format for the sample
            sample_test_file = f"{args.input_file}.sample_test_{sample_size}.json"
            convert_to_test_format(sample, sample_test_file)
        
        # Print first few reactions as example
        print(f"\nFirst 3 reactions as example:")
        for i, r in enumerate(reactions[:3], 1):
            print(f"\n{i}. ID: {r['id']}")
            print(f"   Reactants: {r['reactants']['smiles'][:80]}...")
            if r['reagents']['smiles']:
                print(f"   Reagents: {r['reagents']['smiles'][:80]}...")
            print(f"   Products: {r['products']['smiles'][:80]}...")
            print(f"   Compounds: {r['reactants']['count']} → {r['products']['count']}")

if __name__ == "__main__":
    main()