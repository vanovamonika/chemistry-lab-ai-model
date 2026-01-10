import requests
import json

base_url = "http://localhost:8000"

# # 1. Predict inorganic
# inorganic_response = requests.post(
#     f"{base_url}/predict/products",
#     json={"reactants": "CuSO4 + Zn"}
# )
# print("Inorganic:")
# print(json.dumps(inorganic_response.json(), indent=2))

# # 2. Predict organic  
# organic_response = requests.post(
#     f"{base_url}/predict/products",
#     json={
#         "reactants": "ethene + bromine",
#         "format": "names"
#     }
# )
# print("Organic:")
# print(json.dumps(organic_response.json(), indent=2))

# 3. Predict visual
visual_response = requests.post(
    f"{base_url}/predict/reaction_visuals",
    json={
        "reaction": "CuSO4 + Zn -> Cu + ZnSO4",
        "products": "Cu, ZnSO4",
        "reactant_visuals": "{\"CuSO4\": {\"color\": \"#55aaff, \"state\": \"aqueous solution\"}, \"Zn\": {\"color\": \"#cccccc, \"state\": \"solid\"}}",
        "conditions": "standard laboratory conditions"
    }
)
print("Visual:")
print(visual_response)
# print(visual_response.json())
print(json.dumps(visual_response.json(), indent=3))