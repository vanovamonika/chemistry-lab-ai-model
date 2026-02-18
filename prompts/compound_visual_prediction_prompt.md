As an expert chemist using previously provided knowledge, describe the physical appearance of {compound} at room temperature.
Use the knowledge previously provided and be concise and accurate.
If the compound is colorless, put #ffffff as the hex code and "colorless" as the color (one word). 
If the compound state is solid, provide an information whether it's soluble in water or not (just set "soluble_in_water" true/false), 
if the state is liquid, set "soluble_in_water" to null.
So for colorless compounds, the answer should be:
{{
    "color_hex": "#ffffff",
    "color_string": "colorless",
    "state": "solid/liquid/gas/powder/aqueous solution",
    "soluble_in_water": true/false
}}
Otherwise, provide the hex code of the color and a one or two word description of the color

Give me the color and state of the chemical compound in the form of the following JSON structure without any additional text:
{{
    "color_hex": "hex code",
    "color_string": "one or two word description of the color",
    "state": "solid/liquid/gas/powder/aqueous solution",
    "soluble_in_water": true/false - only for solids, otherwise null
}}