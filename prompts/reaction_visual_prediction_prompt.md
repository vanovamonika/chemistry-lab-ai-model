You are in a chemistry lab. Describe the visual appearance changes during this reaction: {reaction}. 
The reaction takes place in a standard glass beaker at room temperature and atmospheric pressure.
Each chemical is in its typical state (solid, liquid, gas) at room temperature unless otherwise specified, 
crystalline solids are in aqueous solution form unless otherwise specified.
If there are no changes in a particular characteristic, indicate "no change" for that characteristic.
All the color descriptions should be as short and specific as possible.

Return as JSON with this structure:
{{
    initial:
        color: "string", - color description of all reactants and reagents before the reaction
        state: "solid/liquid/gas/powder/crystalline", - state of all the reactants and reagents in the mixture before the reaction 
        bubbles: true/false, - whether there are bubbles present before the reaction
        precipitation: 
            color: "string", - color description of any precipitate present before the reaction
    reaction:
        color: "string", - color change description during the reaction
        state: "solid/liquid/gas/powder/crystalline", - state change description during the reaction
        bubbles: true/false, - whether bubbles are formed during the reaction
        precipitation: 
            color: "string", - color description of any precipitate formed during the reaction
    final:
        color: "string", - color description of all products after the reaction
        state: "solid/liquid/gas/powder/crystalline", - state of all the products after the reaction 
        bubbles: true/false, - whether there are bubbles present after the reaction
        precipitation: 
            color: "string", - color description of any precipitate present after the reaction
    "timing": "string",
    "special_effects": ["array of effects"]
}}

Respond only with the JSON structure, without any additional text.