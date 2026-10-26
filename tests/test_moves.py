import pytest

from moves import TYPE_MOVES, get_moves_for_pokemon
from stats import TYPE_BASE_STATS


@pytest.mark.parametrize("pokemon_type", TYPE_BASE_STATS)
def test_every_type_has_a_guaranteed_starter(monkeypatch, pokemon_type):
    monkeypatch.setattr("moves.random", lambda: 0.99)
    assert get_moves_for_pokemon(pokemon_type, 100) == [TYPE_MOVES[pokemon_type][0]["name"]]


def test_move_catalogue():
    assert TYPE_MOVES.keys() == TYPE_BASE_STATS.keys()
    names = [move["name"] for moves in TYPE_MOVES.values() for move in moves]
    assert len(names) == len(set(names)) == 144
    assert all(len(moves) == 8 for moves in TYPE_MOVES.values())


@pytest.mark.parametrize("pokemon_type", TYPE_BASE_STATS)
def test_learning_is_restricted_to_own_type(monkeypatch, pokemon_type):
    monkeypatch.setattr("moves.random", lambda: 0.0)
    learned = set(get_moves_for_pokemon(pokemon_type, 100))
    assert learned == {move["name"] for move in TYPE_MOVES[pokemon_type]}
    for other_type, moves in TYPE_MOVES.items():
        if other_type != pokemon_type:
            assert learned.isdisjoint(move["name"] for move in moves)


def test_moves_are_unavailable_before_minimum_level(monkeypatch):
    monkeypatch.setattr("moves.random", lambda: 0.0)
    assert get_moves_for_pokemon("Fire", 4) == ["Ember"]
    assert get_moves_for_pokemon("Fire", 9) == ["Ember", "Incinerate"]
    assert get_moves_for_pokemon("Fire", 24) == ["Ember", "Incinerate", "Flame Burst", "Fire Fang"]
    assert get_moves_for_pokemon("Fire", 25) == ["Ember", "Incinerate", "Flame Burst", "Fire Fang", "Flamethrower"]


def test_missed_move_gets_another_chance_next_level(monkeypatch):
    rolls = iter([0.9, 0.1])
    monkeypatch.setattr("moves.random", lambda: next(rolls))
    assert get_moves_for_pokemon("Fire", 11, previous_level=9, known_moves=["Ember", "Incinerate"]) == ["Flame Burst"]


def test_level_jump_rolls_once_per_eligible_level(monkeypatch):
    rolls = []

    def miss():
        rolls.append(1)
        return 0.99

    monkeypatch.setattr("moves.random", miss)
    assert get_moves_for_pokemon("Fire", 30, previous_level=9, known_moves=["Ember", "Incinerate"]) == []
    assert len(rolls) == 21 + 6 + 16  # Available from levels 10, 25, and 15.


def test_eligible_moves_roll_independently(monkeypatch):
    rolls = iter([0.9, 0.0])
    monkeypatch.setattr("moves.random", lambda: next(rolls))
    assert get_moves_for_pokemon("Fire", 25, previous_level=24, known_moves=["Ember", "Incinerate", "Fire Fang"]) == ["Flamethrower"]


def test_known_moves_and_unchanged_levels_do_not_roll(monkeypatch):
    def unexpected_roll():
        pytest.fail("Should not roll for known moves or unchanged levels")

    monkeypatch.setattr("moves.random", unexpected_roll)
    assert get_moves_for_pokemon("Fire", 20, previous_level=20) == []
    assert get_moves_for_pokemon("Fire", 100, known_moves=[move["name"] for move in TYPE_MOVES["Fire"]]) == []
