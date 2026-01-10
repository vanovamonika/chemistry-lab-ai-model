You are in a chemistry lab. Describe the visual appearance changes during this reaction: {reaction}.

The products of the reaction are: {products}.
Visual description of the reactants before the reaction: {reactant_visuals}.

The reaction takes place in a standard glass beaker at room temperature and atmospheric pressure.
crystalline solids are in aqueous solution form and all metals are in their elemental solid form.
All other chemicals are in their typical state (solid, liquid, gas) at room temperature.
If there are no changes in a particular characteristic, indicate "no change" for that characteristic.
All the color descriptions should be as short and specific as possible.

Return as JSON with this structure:
{{
    middle_of_reaction:
        color: "string", color of the mixture as hex code and then string (one or two word), separated by comma
        state: "solid/liquid/gas/powder/aqueous solution", - state of the mixture during the reaction
        solid_elements: 
            color: "string", - if a solid element is present, color of the solid_element as hex code and then string (one or two word),
            separated by comma, otherwise "none", if multiple solid elements are present, separate colors by semicolon
        bubbles: true/false, - whether bubbles are formed during the reaction
        precipitation: 
            color: "string", - color description of any precipitate formed during the reaction
    final_state:
        color: "string", color of the mixture as hex code and then string (one or two word), separated by comma
        state: "solid/liquid/gas/powder/aqueous solution", - state of the mixture during the reaction
        solid_elements: 
            color: "string", - if a solid element is present, color of the solid_element as hex code and then string (one or two word),
            separated by comma, otherwise "none", if multiple solid elements are present, separate colors by semicolon
        bubbles: true/false, - whether there are bubbles present after the reaction and from which compound
        precipitation: 
            color: "string", - color of the precipitate as hex code and then string (one or two word), separated by comma
    "timing": "string", - time taken for the reaction to complete in seconds, minutes, hours (e.g., "5 seconds", "2 minutes", "1 hour")
}}

Respond only with the JSON structure, without any additional text.