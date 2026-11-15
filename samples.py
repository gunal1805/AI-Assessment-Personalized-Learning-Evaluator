"""Built-in sample data so the app can be demoed instantly."""

SAMPLE_QUESTION = (
    "Explain the process of photosynthesis and why it is important for life on Earth. (10 marks)"
)

SAMPLE_RUBRIC = [
    {"Criterion": "Reactants and products",
     "Description": "States that carbon dioxide and water are used and glucose and oxygen are produced",
     "Max marks": 2.0},
    {"Criterion": "Role of light and chlorophyll",
     "Description": "Explains that chlorophyll in the chloroplasts absorbs light energy which drives the process",
     "Max marks": 3.0},
    {"Criterion": "Two stages",
     "Description": "Distinguishes the light-dependent reactions (thylakoids, producing ATP and NADPH) from the Calvin cycle (stroma, fixing carbon dioxide into sugar)",
     "Max marks": 3.0},
    {"Criterion": "Importance for life",
     "Description": "Explains importance: releases oxygen, forms the base of food chains, removes carbon dioxide",
     "Max marks": 2.0},
]

SAMPLE_RESPONSE = (
    "Photosynthesis is how plants make food. Plants take in carbon dioxide and water, and with the "
    "help of sunlight they make glucose and release oxygen. The green pigment in leaves helps absorb "
    "the sunlight. It is important because animals need the oxygen that plants release."
)

SAMPLE_NOTES_NAME = "sample_notes_photosynthesis.txt"
SAMPLE_NOTES = """Photosynthesis is the process by which green plants, algae and some bacteria convert light energy into chemical energy stored in glucose. The overall reaction uses carbon dioxide and water as reactants and produces glucose and oxygen. Photosynthesis takes place in chloroplasts, which contain the green pigment chlorophyll. Chlorophyll absorbs light energy, mainly in the red and blue parts of the spectrum, and this energy drives the reactions.

Photosynthesis has two linked stages. The light-dependent reactions occur in the thylakoid membranes of the chloroplast. Here light energy splits water molecules (photolysis), releasing oxygen, and the energy is captured in the carriers ATP and NADPH. The light-independent reactions, also called the Calvin cycle, occur in the stroma. They use ATP and NADPH to fix carbon dioxide into three-carbon sugars, which are then built into glucose and other carbohydrates.

Photosynthesis is essential for life on Earth. It releases the oxygen that aerobic organisms need for respiration. It forms the base of almost every food chain, because the glucose produced supplies energy and organic matter to producers and, through feeding, to consumers. It also removes carbon dioxide from the atmosphere, helping to regulate the carbon cycle and climate.

Factors that limit the rate of photosynthesis include light intensity, carbon dioxide concentration and temperature. At low light intensity the rate rises with light until another factor becomes limiting.
"""
