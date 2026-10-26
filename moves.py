from random import random


# Learning levels and chances are custom rules for this project.
TYPE_MOVES = {
    "Normal": [
        {"name": "Tackle", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Headbutt", "power": 70, "min_level": 10, "chance": 0.2},
        {"name": "Body Slam", "power": 85, "min_level": 25, "chance": 0.1},
        {"name": "Quick Attack", "power": 40, "min_level": 5, "chance": 0.2},
        {"name": "Swift", "power": 60, "min_level": 15, "chance": 0.15},
        {"name": "Slash", "power": 70, "min_level": 35, "chance": 0.1},
        {"name": "Hyper Voice", "power": 90, "min_level": 50, "chance": 0.08},
        {"name": "Hyper Beam", "power": 150, "min_level": 65, "chance": 0.05},
    ],
    "Fire": [
        {"name": "Ember", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Flame Burst", "power": 70, "min_level": 10, "chance": 0.2},
        {"name": "Flamethrower", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Incinerate", "power": 60, "min_level": 5, "chance": 0.2},
        {"name": "Fire Fang", "power": 65, "min_level": 15, "chance": 0.15},
        {"name": "Fire Punch", "power": 75, "min_level": 35, "chance": 0.1},
        {"name": "Heat Wave", "power": 95, "min_level": 50, "chance": 0.08},
        {"name": "Fire Blast", "power": 110, "min_level": 65, "chance": 0.05},
    ],
    "Water": [
        {"name": "Water Gun", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Bubble Beam", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Surf", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Aqua Jet", "power": 40, "min_level": 5, "chance": 0.2},
        {"name": "Water Pulse", "power": 60, "min_level": 15, "chance": 0.15},
        {"name": "Aqua Tail", "power": 90, "min_level": 35, "chance": 0.1},
        {"name": "Liquidation", "power": 85, "min_level": 50, "chance": 0.08},
        {"name": "Hydro Pump", "power": 110, "min_level": 65, "chance": 0.05},
    ],
    "Electric": [
        {"name": "Thunder Shock", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Spark", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Thunderbolt", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Nuzzle", "power": 20, "min_level": 5, "chance": 0.2},
        {"name": "Shock Wave", "power": 60, "min_level": 15, "chance": 0.15},
        {"name": "Thunder Punch", "power": 75, "min_level": 35, "chance": 0.1},
        {"name": "Discharge", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Thunder", "power": 110, "min_level": 65, "chance": 0.05},
    ],
    "Grass": [
        {"name": "Vine Whip", "power": 45, "min_level": 1, "chance": 1.0},
        {"name": "Razor Leaf", "power": 55, "min_level": 10, "chance": 0.2},
        {"name": "Energy Ball", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Absorb", "power": 20, "min_level": 5, "chance": 0.2},
        {"name": "Mega Drain", "power": 40, "min_level": 15, "chance": 0.15},
        {"name": "Giga Drain", "power": 75, "min_level": 35, "chance": 0.1},
        {"name": "Leaf Blade", "power": 90, "min_level": 50, "chance": 0.08},
        {"name": "Solar Beam", "power": 120, "min_level": 65, "chance": 0.05},
    ],
    "Ice": [
        {"name": "Powder Snow", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Aurora Beam", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Ice Beam", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Ice Shard", "power": 40, "min_level": 5, "chance": 0.2},
        {"name": "Icy Wind", "power": 55, "min_level": 15, "chance": 0.15},
        {"name": "Ice Fang", "power": 65, "min_level": 35, "chance": 0.1},
        {"name": "Ice Punch", "power": 75, "min_level": 50, "chance": 0.08},
        {"name": "Blizzard", "power": 110, "min_level": 65, "chance": 0.05},
    ],
    "Fighting": [
        {"name": "Mach Punch", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Brick Break", "power": 75, "min_level": 10, "chance": 0.2},
        {"name": "Close Combat", "power": 120, "min_level": 25, "chance": 0.1},
        {"name": "Low Sweep", "power": 65, "min_level": 5, "chance": 0.2},
        {"name": "Force Palm", "power": 60, "min_level": 15, "chance": 0.15},
        {"name": "Drain Punch", "power": 75, "min_level": 35, "chance": 0.1},
        {"name": "Aura Sphere", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Focus Blast", "power": 120, "min_level": 65, "chance": 0.05},
    ],
    "Poison": [
        {"name": "Poison Sting", "power": 15, "min_level": 1, "chance": 1.0},
        {"name": "Venoshock", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Sludge Bomb", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Smog", "power": 30, "min_level": 5, "chance": 0.2},
        {"name": "Acid", "power": 40, "min_level": 15, "chance": 0.15},
        {"name": "Poison Fang", "power": 50, "min_level": 35, "chance": 0.1},
        {"name": "Poison Jab", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Gunk Shot", "power": 120, "min_level": 65, "chance": 0.05},
    ],
    "Ground": [
        {"name": "Mud-Slap", "power": 20, "min_level": 1, "chance": 1.0},
        {"name": "Bulldoze", "power": 60, "min_level": 10, "chance": 0.2},
        {"name": "Earthquake", "power": 100, "min_level": 25, "chance": 0.1},
        {"name": "Mud Shot", "power": 55, "min_level": 5, "chance": 0.2},
        {"name": "Bone Club", "power": 65, "min_level": 15, "chance": 0.15},
        {"name": "Dig", "power": 80, "min_level": 35, "chance": 0.1},
        {"name": "Drill Run", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Earth Power", "power": 90, "min_level": 65, "chance": 0.05},
    ],
    "Flying": [
        {"name": "Gust", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Wing Attack", "power": 60, "min_level": 10, "chance": 0.2},
        {"name": "Air Slash", "power": 75, "min_level": 25, "chance": 0.1},
        {"name": "Peck", "power": 35, "min_level": 5, "chance": 0.2},
        {"name": "Aerial Ace", "power": 60, "min_level": 15, "chance": 0.15},
        {"name": "Pluck", "power": 60, "min_level": 35, "chance": 0.1},
        {"name": "Drill Peck", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Hurricane", "power": 110, "min_level": 65, "chance": 0.05},
    ],
    "Psychic": [
        {"name": "Confusion", "power": 50, "min_level": 1, "chance": 1.0},
        {"name": "Psybeam", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Psychic", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Stored Power", "power": 20, "min_level": 5, "chance": 0.2},
        {"name": "Psyshock", "power": 80, "min_level": 15, "chance": 0.15},
        {"name": "Zen Headbutt", "power": 80, "min_level": 35, "chance": 0.1},
        {"name": "Extrasensory", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Future Sight", "power": 120, "min_level": 65, "chance": 0.05},
    ],
    "Bug": [
        {"name": "Struggle Bug", "power": 50, "min_level": 1, "chance": 1.0},
        {"name": "Bug Bite", "power": 60, "min_level": 10, "chance": 0.2},
        {"name": "Bug Buzz", "power": 90, "min_level": 25, "chance": 0.1},
        {"name": "Fury Cutter", "power": 40, "min_level": 5, "chance": 0.2},
        {"name": "Pin Missile", "power": 25, "min_level": 15, "chance": 0.15},
        {"name": "Silver Wind", "power": 60, "min_level": 35, "chance": 0.1},
        {"name": "X-Scissor", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Megahorn", "power": 120, "min_level": 65, "chance": 0.05},
    ],
    "Rock": [
        {"name": "Rock Throw", "power": 50, "min_level": 1, "chance": 1.0},
        {"name": "Rock Tomb", "power": 60, "min_level": 10, "chance": 0.2},
        {"name": "Rock Slide", "power": 75, "min_level": 25, "chance": 0.1},
        {"name": "Rollout", "power": 30, "min_level": 5, "chance": 0.2},
        {"name": "Rock Blast", "power": 25, "min_level": 15, "chance": 0.15},
        {"name": "Ancient Power", "power": 60, "min_level": 35, "chance": 0.1},
        {"name": "Power Gem", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Stone Edge", "power": 100, "min_level": 65, "chance": 0.05},
    ],
    "Ghost": [
        {"name": "Lick", "power": 30, "min_level": 1, "chance": 1.0},
        {"name": "Hex", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Shadow Ball", "power": 80, "min_level": 25, "chance": 0.1},
        {"name": "Astonish", "power": 30, "min_level": 5, "chance": 0.2},
        {"name": "Shadow Sneak", "power": 40, "min_level": 15, "chance": 0.15},
        {"name": "Shadow Punch", "power": 60, "min_level": 35, "chance": 0.1},
        {"name": "Ominous Wind", "power": 60, "min_level": 50, "chance": 0.08},
        {"name": "Phantom Force", "power": 90, "min_level": 65, "chance": 0.05},
    ],
    "Dragon": [
        {"name": "Twister", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Dragon Breath", "power": 60, "min_level": 10, "chance": 0.2},
        {"name": "Dragon Pulse", "power": 85, "min_level": 25, "chance": 0.1},
        {"name": "Dragon Tail", "power": 60, "min_level": 5, "chance": 0.2},
        {"name": "Dragon Claw", "power": 80, "min_level": 15, "chance": 0.15},
        {"name": "Dragon Rush", "power": 100, "min_level": 35, "chance": 0.1},
        {"name": "Outrage", "power": 120, "min_level": 50, "chance": 0.08},
        {"name": "Draco Meteor", "power": 130, "min_level": 65, "chance": 0.05},
    ],
    "Dark": [
        {"name": "Bite", "power": 60, "min_level": 1, "chance": 1.0},
        {"name": "Night Slash", "power": 70, "min_level": 10, "chance": 0.2},
        {"name": "Dark Pulse", "power": 80, "min_level": 25, "chance": 0.1},
        {"name": "Assurance", "power": 60, "min_level": 5, "chance": 0.2},
        {"name": "Feint Attack", "power": 60, "min_level": 15, "chance": 0.15},
        {"name": "Knock Off", "power": 65, "min_level": 35, "chance": 0.1},
        {"name": "Crunch", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Foul Play", "power": 95, "min_level": 65, "chance": 0.05},
    ],
    "Steel": [
        {"name": "Metal Claw", "power": 50, "min_level": 1, "chance": 1.0},
        {"name": "Mirror Shot", "power": 65, "min_level": 10, "chance": 0.2},
        {"name": "Flash Cannon", "power": 80, "min_level": 25, "chance": 0.1},
        {"name": "Bullet Punch", "power": 40, "min_level": 5, "chance": 0.2},
        {"name": "Smart Strike", "power": 70, "min_level": 15, "chance": 0.15},
        {"name": "Steel Wing", "power": 70, "min_level": 35, "chance": 0.1},
        {"name": "Iron Head", "power": 80, "min_level": 50, "chance": 0.08},
        {"name": "Iron Tail", "power": 100, "min_level": 65, "chance": 0.05},
    ],
    "Fairy": [
        {"name": "Fairy Wind", "power": 40, "min_level": 1, "chance": 1.0},
        {"name": "Draining Kiss", "power": 50, "min_level": 10, "chance": 0.2},
        {"name": "Moonblast", "power": 95, "min_level": 25, "chance": 0.1},
        {"name": "Disarming Voice", "power": 40, "min_level": 5, "chance": 0.2},
        {"name": "Dazzling Gleam", "power": 80, "min_level": 15, "chance": 0.15},
        {"name": "Spirit Break", "power": 75, "min_level": 35, "chance": 0.1},
        {"name": "Play Rough", "power": 90, "min_level": 50, "chance": 0.08},
        {"name": "Alluring Voice", "power": 80, "min_level": 65, "chance": 0.05},
    ],
}


def get_moves_for_pokemon(
    pokemon_type: str, level: int, previous_level: int = 0, known_moves=()
):
    """Return newly learned move names, rolling once per gained level."""
    learned = set(known_moves)
    new_moves = []

    for gained_level in range(previous_level + 1, level + 1):
        for move in TYPE_MOVES[pokemon_type]:
            if move["name"] in learned or gained_level < move["min_level"]:
                continue
            if move["chance"] == 1.0 or random() < move["chance"]:
                learned.add(move["name"])
                new_moves.append(move["name"])

    return new_moves
