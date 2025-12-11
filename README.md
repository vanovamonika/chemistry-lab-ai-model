# AI model for predicting results of chemical reactions

## Install dependencies

1. Do the following before installing the dependencies found in `requirements.txt` file:

```python
pip install --upgrade pip
pip install virtualenv
virtualenv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

2. Now run this command to install dependenies in the `requirements.txt` file. 

```python
pip install -r requirements.txt
```

## Create database

Create the Chroma DB.

```python
python create_database.py
```

## Run reaction prediction

Run the main script with defined reactants, reaction type (organic/inorganic) and optional parameters describing the reaction conditions.
For organic reactions it is necessary to define the input format of the reactants (smiles/names, default: smiles).

- organic reaction example:
```python
python main.py --reactants "reactant_name_1 + reactant_name_2" --format "names" --type "organic" [optional_parameters]
```

- inorganic reaction example:
```python
python main.py --reactants "reactant_smiles_1 + reactant_smiles_2" --type "inorganic" [optional_parameters]
```

optional parameters are following:
- --reagents: Reagents used in the reaction (default: None)
- --temperature: Temperature of the reaction in Celsius (default 20)
- --conditions: Chemical reaction conditions description (default: None)
