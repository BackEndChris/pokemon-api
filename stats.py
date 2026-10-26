from random import randint


TYPE_BASE_STATS = {
    "Normal": {
        "hp": 70,
        "attack": 65,
        "defense": 60,
        "special_attack": 50,
        "special_defense": 55,
        "speed": 60,
    },
    "Fire": {
        "hp": 55,
        "attack": 65,
        "defense": 45,
        "special_attack": 80,
        "special_defense": 55,
        "speed": 60,
    },
    "Water": {
        "hp": 70,
        "attack": 55,
        "defense": 65,
        "special_attack": 65,
        "special_defense": 65,
        "speed": 40,
    },
    "Electric": {
        "hp": 50,
        "attack": 55,
        "defense": 45,
        "special_attack": 80,
        "special_defense": 50,
        "speed": 80,
    },
    "Grass": {
        "hp": 65,
        "attack": 55,
        "defense": 65,
        "special_attack": 70,
        "special_defense": 65,
        "speed": 40,
    },
    "Ice": {
        "hp": 50,
        "attack": 60,
        "defense": 45,
        "special_attack": 80,
        "special_defense": 65,
        "speed": 60,
    },
    "Fighting": {
        "hp": 80,
        "attack": 80,
        "defense": 60,
        "special_attack": 40,
        "special_defense": 50,
        "speed": 50,
    },
    "Poison": {
        "hp": 65,
        "attack": 60,
        "defense": 60,
        "special_attack": 65,
        "special_defense": 65,
        "speed": 45,
    },
    "Ground": {
        "hp": 75,
        "attack": 75,
        "defense": 70,
        "special_attack": 45,
        "special_defense": 50,
        "speed": 45,
    },
    "Flying": {
        "hp": 55,
        "attack": 65,
        "defense": 50,
        "special_attack": 55,
        "special_defense": 55,
        "speed": 80,
    },
    "Psychic": {
        "hp": 50,
        "attack": 40,
        "defense": 50,
        "special_attack": 75,
        "special_defense": 80,
        "speed": 65,
    },
    "Bug": {
        "hp": 60,
        "attack": 65,
        "defense": 60,
        "special_attack": 45,
        "special_defense": 50,
        "speed": 80,
    },
    "Rock": {
        "hp": 65,
        "attack": 80,
        "defense": 85,
        "special_attack": 40,
        "special_defense": 50,
        "speed": 40,
    },
    "Ghost": {
        "hp": 50,
        "attack": 45,
        "defense": 50,
        "special_attack": 80,
        "special_defense": 70,
        "speed": 65,
    },
    "Dragon": {
        "hp": 60,
        "attack": 70,
        "defense": 55,
        "special_attack": 70,
        "special_defense": 55,
        "speed": 50,
    },
    "Dark": {
        "hp": 60,
        "attack": 75,
        "defense": 50,
        "special_attack": 60,
        "special_defense": 50,
        "speed": 65,
    },
    "Steel": {
        "hp": 60,
        "attack": 60,
        "defense": 85,
        "special_attack": 40,
        "special_defense": 80,
        "speed": 35,
    },
    "Fairy": {
        "hp": 65,
        "attack": 45,
        "defense": 55,
        "special_attack": 75,
        "special_defense": 75,
        "speed": 45,
    },
}


def calculate_stats(pokemon_type: str, level: int):
    """Roll a small variation for each stat when creating a Pokemon."""
    base = TYPE_BASE_STATS[pokemon_type]

    return {
        stat: value + randint(-4, 4) + level * (3 if stat == "hp" else 2)
        for stat, value in base.items()
    }
