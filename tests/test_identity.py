from pokemon_oop_explorer.models.value_objects import PokemonIdentity


def test_shiny_computation_xor_values() -> None:
    identity = PokemonIdentity(trainer_id=1, secret_id=2, personality_value=0x00030004)
    report = identity.shiny_report()
    assert report.pid_high == 3
    assert report.pid_low == 4
    assert report.shiny_value == (1 ^ 2 ^ 3 ^ 4)


def test_shiny_threshold() -> None:
    identity = PokemonIdentity(
        trainer_id=12345, secret_id=54321, personality_value=0xABCD1234
    )
    report = identity.shiny_report()
    assert report.is_shiny is (report.shiny_value < 8)
