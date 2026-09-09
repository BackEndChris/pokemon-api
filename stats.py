TYPE_BASE_STATS = {
    "Fire": {
        "hp": 45,
        "attack": 60,
        "defense": 40,
        "speed": 65
    },
    "Water": {
        "hp": 55,
        "attack": 50,
        "defense": 60,
        "speed": 45
    },
    "Grass": {
        "hp": 60,
        "attack": 45,
        "defense": 55,
        "speed": 40
    }
}

def calculate_stats(pokemon_type: str, level: int):
    base = TYPE_BASE_STATS[pokemon_type]

    return {
        "hp": base["hp"] + level * 3,
        "attack": base["attack"] + level * 2,
        "defense": base["defense"] + level * 2,
        "speed": base["speed"] + level * 2
    }