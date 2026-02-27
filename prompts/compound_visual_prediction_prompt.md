As an expert chemist using previously provided knowledge, describe the physical appearance of the chemical with formula {formula}, name {name} at room temperature.
Use the knowledge previously provided and be concise and accurate.
If the compound is colorless, put #ffffff as the hex code and "colorless" as the color (one word). 
If the compound state is solid, provide an information whether it's soluble in water or not (just set "soluble_in_water" true/false), 
if the state is liquid, set "soluble_in_water" to null.

Return ONLY this exact JSON structure with NO additional text:
{{
    "color_hex": "hex code (e.g., #ffffff for colorless)",
    "color": "one or two word description of the color",
    "state": "solid/liquid/gas/powder/aqueous solution",
    "soluble_in_water": true/false/null
}}