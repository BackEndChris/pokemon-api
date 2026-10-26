import pytest

from stats import TYPE_BASE_STATS, calculate_stats


@pytest.mark.parametrize("pokemon_type", TYPE_BASE_STATS)
@pytest.mark.parametrize("variation", [-4, 0, 4])
def test_stat_variation_and_level_growth(monkeypatch, pokemon_type, variation):
    def fixed_roll(low, high):
        assert (low, high) == (-4, 4)
        return variation

    monkeypatch.setattr("stats.randint", fixed_roll)

    for level in (1, 20, 100):
        result = calculate_stats(pokemon_type, level)
        for stat, base in TYPE_BASE_STATS[pokemon_type].items():
            growth = 3 if stat == "hp" else 2
            assert result[stat] == base + variation + level * growth


def test_archetypes_have_equal_budgets():
    assert len(TYPE_BASE_STATS) == 18
    assert all(sum(base.values()) == 360 for base in TYPE_BASE_STATS.values())
