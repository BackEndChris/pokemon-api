TYPE_MOVES = {
    "Fire": [
        {"name": "Ember", "min_level": 1},
        {"name": "Flame Burst", "min_level": 10}
    ],
    "Water": [
        {"name": "Water Gun", "min_level": 1},
        {"name": "Bubble Beam", "min_level": 10}
    ],
    "Grass": [
        {"name": "Vine Whip", "min_level": 1},
        {"name": "Razor Leaf", "min_level": 10}
    ]
}


def get_moves_for_pokemon(pokemon_type: str, level: int):
    available_moves = []

    for move in TYPE_MOVES[pokemon_type]:
        if level >= move["min_level"]:
            available_moves.append(move["name"])

    return available_moves