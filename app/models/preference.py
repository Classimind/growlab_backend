from enum import Enum


class PreferenceMode(str, Enum):
    BALANCED = "balanced"
    GROWTH = "growth"
    WATER_SAVE = "water_save"
    ENERGY_SAVE = "energy_save"
    NUTRIENT_STABILITY = "nutrient_stability"
    CUSTOM = "custom"


from enum import Enum


class TargetPlant(str, Enum):
    # Leafy greens
    LETTUCE = "lettuce"
    SPINACH = "spinach"
    KALE = "kale"
    ARUGULA = "arugula"
    BOK_CHOY = "bok_choy"
    BASIL = "basil"
    MINT = "mint"

    # Fruiting plants
    TOMATO = "tomato"
    STRAWBERRY = "strawberry"
    CUCUMBER = "cucumber"
    BELL_PEPPER = "bell_pepper"
    CHILI_PEPPER = "chili_pepper"

    # Herbs
    ROSEMARY = "rosemary"
    OREGANO = "oregano"
    THYME = "thyme"

    # Microgreens
    RADISH_MICROGREEN = "radish_microgreen"
    BROCCOLI_MICROGREEN = "broccoli_microgreen"

    # Root vegetables
    CARROT = "carrot"
    RADISH = "radish"