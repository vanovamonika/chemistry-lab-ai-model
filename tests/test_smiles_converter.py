import unittest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
import requests

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import smiles_converter

class TestSmilesConverter(unittest.TestCase):
    """Test SMILES conversion functions"""
    
    def test_clean_smiles(self):
        """Test SMILES string cleaning"""
        test_cases = [
            ("[Na +]", "[Na+]"),
            ("[OH - ]", "[OH-]"),
            ("C C O", "CCO"),
            ("c1ccccc1\n", "c1ccccc1"),
        ]
        
        for input_smiles, expected in test_cases:
            with self.subTest(input_smiles=input_smiles):
                result = smiles_converter.clean_smiles(input_smiles)
                self.assertEqual(result, expected)
    
    def test_is_likely_smiles(self):
        """Test SMILES pattern detection"""
        self.assertTrue(smiles_converter.is_likely_smiles("CCO"))
        self.assertTrue(smiles_converter.is_likely_smiles("c1ccccc1"))
        self.assertTrue(smiles_converter.is_likely_smiles("[Na+]"))
        self.assertFalse(smiles_converter.is_likely_smiles("ethanol"))
        self.assertFalse(smiles_converter.is_likely_smiles("sodium hydroxide"))
    
    @patch('smiles_converter.requests.get')
    def test_chemical_name_to_smiles_success(self, mock_get):
        """Test successful name to SMILES conversion"""
        # Mock PubChem CID response
        mock_cid_response = Mock()
        mock_cid_response.json.return_value = {
            'IdentifierList': {'CID': [12345]}
        }
        
        # Mock PubChem SMILES response
        mock_smiles_response = Mock()
        mock_smiles_response.json.return_value = {
            'PropertyTable': {
                'Properties': [{'ConnectivitySMILES': 'CCO'}]
            }
        }
        
        mock_get.side_effect = [mock_cid_response, mock_smiles_response]
        
        result = smiles_converter.chemical_name_to_smiles('ethanol')
        self.assertEqual(result, 'CCO')
    
    @patch('smiles_converter.requests.get')
    def test_smiles_to_chemical_name_success(self, mock_get):
        """Test successful SMILES to name conversion"""
        # Mock PubChem CID response
        mock_cid_response = Mock()
        mock_cid_response.status_code = 200
        mock_cid_response.json.return_value = {
            'IdentifierList': {'CID': [12345]}
        }
        
        # Mock PubChem name response
        mock_name_response = Mock()
        mock_name_response.status_code = 200
        mock_name_response.json.return_value = {
            'PropertyTable': {
                'Properties': [{
                    'IUPACName': 'ethanol',
                    'Title': 'Ethanol'
                }]
            }
        }
        
        mock_get.side_effect = [mock_cid_response, mock_name_response]
        
        result = smiles_converter.smiles_to_chemical_name('CCO')
        self.assertEqual(result, 'ethanol')
    
    def test_get_smile_reaction_formula_from_names(self):
        """Test reaction formula conversion from names"""
        with patch.object(smiles_converter, 'chemical_name_to_smiles') as mock_converter:
            mock_converter.side_effect = ['CCO', 'CC(=O)O']
            
            result = smiles_converter.get_smile_reaction_formula_from_names('ethanol+acetic acid')
            self.assertEqual(result, 'CCO.CC(=O)O')
    
    def test_get_name_reaction_formula_from_smiles(self):
        """Test reaction formula conversion from SMILES"""
        with patch.object(smiles_converter, 'smiles_to_chemical_name') as mock_converter:
            mock_converter.side_effect = ['ethanol', 'acetic acid']
            
            result = smiles_converter.get_name_reaction_formula_from_smiles('CCO.CC(=O)O')
            self.assertEqual(result, 'ethanol + acetic acid')