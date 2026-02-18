You are in a chemistry lab. Describe the visual appearance changes during this reaction: {reaction}.

The products of the reaction are: {products}.
Visual description of the reactants before the reaction: {reactant_visuals}.

The reaction takes place in a standard glass beaker at room temperature and atmospheric pressure.
crystalline solids are in aqueous solution form and all metals are in their elemental solid form.
All other chemicals are in their typical state (solid, liquid, gas) at room temperature.
If there are no changes in a particular characteristic, indicate "no change" for that characteristic.
All the color descriptions should be as short and specific as possible.
If the solution is colorless, put #ffffff as the hex code (color_hex json field) 
and "colorless" as the color description (one or two words in the color json field).
so the color item for colorless solutions should be:

"color": "#ffffff,colorless",

Return as JSON with this structure:
{{
    middle_of_reaction: - description of the visual appearance of the reaction mixture at the point when the reaction is actively occurring, including any changes in color, state, formation of bubbles, precipitates, or solid elements.
        color_hex: color of the mixture as hex code
        color: color description of the mixture (one or two word)
        state: "solid/liquid/gas/powder/aqueous solution", - state of the mixture during the reaction
        solid_elements: 
            color_hex: "string", - if a solid element that doesnt disolve (like metal) is one of the products, color of the solid_element as hex code, otherwise "none" 
            color: "string", - if a solid element that doesnt disolve (like metal) is one of the products, color description of the solid_element (one or two word), otherwise "none", 
            formula: "string", - if a solid element that doesnt disolve (like metal) is one of the products, chemical formula of the solid element product, otherwise "none"
        bubbles: true/false, - whether bubbles are formed during the reaction
        precipitation: 
            color_hex: "string", - if any of the products forms a precipitate, color hex code of the precipitate, otherwise "none"
            color: "string", - if any of the products forms a precipitate, color description of the precipitate, otherwise "none"
            formula: "string", - if any of the products forms a precipitate, chemical formula of the precipitate product, otherwise "none"
    final_state: - description of the visual appearance of the reaction mixture at the end of the reaction, including any changes in color, state, formation of bubbles, precipitates, or solid elements.
        color_hex: "string", color of the mixture as hex code
        color: "string", color description of the mixture (one or two word)
        state: "solid/liquid/gas/powder/aqueous solution", - state of the mixture during the reaction
        solid_elements: 
            color_hex: "string", - if a solid element that doesnt disolve (like metal) is one of the products, color of the solid_element as hex code, otherwise "none" 
            color: "string", - if a solid element that doesnt disolve (like metal) is one of the products, color description of the solid_element (one or two word), otherwise "none", 
            formula: "string", - if a solid element that doesnt disolve (like metal) is one of the products, chemical formula of the solid element product, otherwise "none"
        bubbles: true/false, - whether there are bubbles present after the reaction
        precipitation: 
            color_hex: "string", - if any of the products forms a precipitate, color hex code of the precipitate, otherwise "none"
            color: "string", - if any of the products forms a precipitate, color description of the precipitate, otherwise "none"
            formula: "string", - if any of the products forms a precipitate, chemical formula of the precipitate product, otherwise "none"
    "timing": "string", - time taken for the reaction to complete in seconds, minutes, hours (e.g., "5 seconds", "2 minutes", "1 hour")
}}

Double check that all fields are filled in correctly and that they are in line with all chemical knowledge and the provided information about the reactants, products, and reaction conditions. 
If there are no changes in a particular characteristic, make sure to indicate "no change" for that characteristic.
Make sure you check that the JSON is valid and only contains the required fields. Respond only with the JSON structure, without any additional text.