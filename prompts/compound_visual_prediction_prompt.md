As an expert chemist using previously provided knowledge, describe the physical appearance of {compound} at room temperature.
Use the knowledge previously provided and be concise and accurate.
If the compound is colorless, put #ffffff as the hex code and "colorless" as the color (one word). 
So for colorless compounds, the answer should be:
{{
    "color": "#ffffff,colorless",
    "state": "solid/liquid/gas/powder/aqueous solution",
}}
Otherwise, provide the hex code of the color and a one or two word description of the color

Give me the color and state of the chemical compound in the form of the following JSON structure without any additional text:
{{
    "color": "string", - color of the compound as hex code and then string (one or two word), separated by comma
    "state": "solid/liquid/gas/powder/aqueous solution",
}}