As an expert chemist, describe the visual appearance changes during this reaction: {reaction}. 
When a metal is part of the reaction, it is in a form of a solid piece (sheet).

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