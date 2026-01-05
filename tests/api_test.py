import requests

# All three endpoints
base_url = "http://localhost:8000"

# 1. Predict inorganic
inorganic_response = requests.post(
    f"{base_url}/predict/inorganic",
    json={"reactants": "H2SO4 + KOH"}
)
print("Inorganic:", inorganic_response.json())

# 2. Predict organic  
organic_response = requests.post(
    f"{base_url}/predict/organic",
    json={
        "reactants": "ethene",
        "reagents": "bromine",
        "format": "names"
    }
)
print("Organic:", organic_response.json())

# 3. Predict visual
visual_response = requests.post(
    f"{base_url}/predict/visual",
    json={
        "type": "reaction",
        "reaction": "CH4 + 2O2 → CO2 + 2H2O"
    }
)
print("Visual:", visual_response.json())