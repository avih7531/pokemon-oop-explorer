"""Seeded domain data for Gen 1-3 starter families."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pokemon_oop_explorer.models.abilities import (
    Ability,
    PassiveAbility,
    TriggeredAbility,
)
from pokemon_oop_explorer.models.effects import (
    AbstractEffect,
    DamageEffect,
    HealEffect,
    StatStageEffect,
    StatusEffect,
)
from pokemon_oop_explorer.models.enums import ElementType, Generation, StatKind
from pokemon_oop_explorer.models.evolution import (
    EvolutionRule,
    FriendshipEvolutionRule,
    ItemEvolutionRule,
    LevelEvolutionRule,
)
from pokemon_oop_explorer.models.items import HeldItem
from pokemon_oop_explorer.models.moves import (
    Move,
    PhysicalMove,
    SpecialMove,
    StatusMove,
)
from pokemon_oop_explorer.models.pokemon import (
    BattleReadyPokemon,
    EvolutionStageSpecies,
    FireStarterPokemon,
    FireStarterSpecies,
    GrassStarterPokemon,
    GrassStarterSpecies,
    PokemonInstance,
    PokemonSpecies,
    WaterStarterPokemon,
    WaterStarterSpecies,
)
from pokemon_oop_explorer.models.status import BurnStatus, ParalysisStatus, PoisonStatus
from pokemon_oop_explorer.models.trainer import Trainer, TrainerIdentity
from pokemon_oop_explorer.models.value_objects import (
    NATURES,
    AttackStat,
    DefenseStat,
    EvolutionLine,
    HPStat,
    Learnset,
    MoveSlot,
    PokemonIdentity,
    SpecialAttackStat,
    SpecialDefenseStat,
    SpeedStat,
    SpriteAsset,
    StatBlock,
    Type,
)


@dataclass(slots=True)
class DomainCatalog:
    species_by_key: dict[str, PokemonSpecies]
    families: dict[str, list[PokemonSpecies]]
    instances: list[PokemonInstance]
    trainers: list[Trainer]


def _type_from_name(type_name: str) -> Type:
    return Type(element=ElementType[type_name.upper().replace("-", "_")])


def _generation_from_name(value: str) -> Generation:
    match value:
        case "generation-i":
            return Generation.GEN_1
        case "generation-ii":
            return Generation.GEN_2
        case _:
            return Generation.GEN_3


def _stats_from_api(stats: dict[str, int]) -> StatBlock:
    return StatBlock(
        hp=HPStat(value=stats["hp"]),
        attack=AttackStat(value=stats["attack"]),
        defense=DefenseStat(value=stats["defense"]),
        special_attack=SpecialAttackStat(value=stats["special-attack"]),
        special_defense=SpecialDefenseStat(value=stats["special-defense"]),
        speed=SpeedStat(value=stats["speed"]),
    )


def _sprite_asset(species_key: str, root: Path) -> SpriteAsset:
    return SpriteAsset(
        species_key=species_key,
        regular_path=root / "sprites" / "regular" / species_key,
        shiny_path=root / "sprites" / "shiny" / species_key,
    )


def _display_name(key: str) -> str:
    return " ".join(part.capitalize() for part in key.split("-"))


_STATUS_MOVE_HINTS: dict[str, type] = {
    "poison-powder": PoisonStatus,
    "poisonpowder": PoisonStatus,
    "toxic": PoisonStatus,
    "stun-spore": ParalysisStatus,
    "thunder-wave": ParalysisStatus,
    "will-o-wisp": BurnStatus,
}


def _effects_for_move(
    name: str, damage_class: str, power: int | None
) -> list[AbstractEffect]:
    effects: list[AbstractEffect] = []
    base = power or 0
    if damage_class == "physical" and base:
        effects.append(
            DamageEffect(
                name=f"{_display_name(name)} Strike", base_damage=max(5, base // 5)
            )
        )
    elif damage_class == "special" and base:
        effects.append(
            DamageEffect(
                name=f"{_display_name(name)} Blast", base_damage=max(5, base // 5)
            )
        )
    elif damage_class == "status":
        condition_factory = _STATUS_MOVE_HINTS.get(name)
        if condition_factory is not None:
            effects.append(
                StatusEffect(
                    name=f"{_display_name(name)} Inflict",
                    condition_factory=condition_factory,
                )
            )
        elif "growl" in name or "leer" in name:
            effects.append(
                StatStageEffect(
                    name=f"{_display_name(name)} Debuff",
                    stat=StatKind.ATTACK if "growl" in name else StatKind.DEFENSE,
                    delta=-1,
                )
            )
        elif "growth" in name or "swords-dance" in name:
            effects.append(
                StatStageEffect(
                    name=f"{_display_name(name)} Boost",
                    stat=StatKind.ATTACK,
                    delta=1,
                    target_self=True,
                )
            )
        elif "recover" in name or "synthesis" in name or "roost" in name:
            effects.append(
                HealEffect(
                    name=f"{_display_name(name)} Heal", heal_amount=25, target_self=True
                )
            )
    return effects


def _build_move(name: str, move_data: dict[str, Any]) -> Move:
    move_type = _type_from_name(move_data["type"])
    pretty_name = _display_name(name)
    damage_class = move_data["damage_class"]
    effects = _effects_for_move(name, damage_class, move_data.get("power"))
    if damage_class == "physical":
        return PhysicalMove(
            name=pretty_name,
            power=move_data["power"],
            accuracy=move_data["accuracy"],
            pp=move_data["pp"],
            move_type=move_type,
            effects=effects,
        )
    if damage_class == "special":
        return SpecialMove(
            name=pretty_name,
            power=move_data["power"],
            accuracy=move_data["accuracy"],
            pp=move_data["pp"],
            move_type=move_type,
            effects=effects,
        )
    return StatusMove(
        name=pretty_name,
        power=move_data["power"],
        accuracy=move_data["accuracy"],
        pp=move_data["pp"],
        move_type=move_type,
        effects=effects,
    )


def _build_ability(
    ability_name: str,
    *,
    is_hidden: bool,
    ability_details: dict[str, dict[str, str]],
    ability_cache: dict[str, Ability],
) -> Ability:
    cache_key = f"{ability_name}:{int(is_hidden)}"
    if cache_key in ability_cache:
        return ability_cache[cache_key]
    effect = ability_details.get(ability_name, {}).get("effect", "")
    pretty_name = _display_name(ability_name)
    if is_hidden:
        ability = TriggeredAbility(
            name=pretty_name,
            effect_summary=effect,
            trigger_condition="Hidden ability slot",
        )
    else:
        ability = PassiveAbility(name=pretty_name, effect_summary=effect)
    ability_cache[cache_key] = ability
    return ability


def _build_rule(target_key: str, trigger: dict[str, Any] | None) -> EvolutionRule:
    if not trigger:
        return LevelEvolutionRule(
            name="Level Evolution", target_species_key=target_key, minimum_level=0
        )
    if trigger.get("item"):
        return ItemEvolutionRule(
            name="Item Evolution",
            target_species_key=target_key,
            required_item_key=trigger["item"],
        )
    if trigger.get("min_happiness") is not None:
        return FriendshipEvolutionRule(
            name="Friendship Evolution",
            target_species_key=target_key,
            minimum_friendship=int(trigger["min_happiness"]),
        )
    return LevelEvolutionRule(
        name="Level Evolution",
        target_species_key=target_key,
        minimum_level=int(trigger.get("min_level") or 0),
    )


def _learnset_for_species(
    species_key: str, raw_pokemon: dict[str, Any], move_catalog: dict[str, Move]
) -> Learnset:
    learnset = Learnset()
    for entry in raw_pokemon[species_key]["level_up_moves"]:
        move = move_catalog.get(entry["name"])
        if move is not None:
            learnset.add_move(int(entry["level"]), move)
    return learnset


def _starter_instance_class(primary_type: ElementType) -> type[PokemonInstance]:
    if primary_type == ElementType.GRASS:
        return GrassStarterPokemon
    if primary_type == ElementType.FIRE:
        return FireStarterPokemon
    return WaterStarterPokemon


def _instance_moves(species: PokemonSpecies, level: int) -> list[MoveSlot]:
    learned = species.learnset.moves_up_to_level(level)
    final_moves = learned[-4:] if len(learned) > 4 else learned
    return [MoveSlot(move=move, current_pp=move.pp) for move in final_moves]


def build_catalog(project_root: Path) -> DomainCatalog:
    cache_path = project_root / "pokeapi_cache.json"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Missing {cache_path}. Run `python -u fetch_pokeapi.py --delay 0.5` first."
        )

    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    raw_pokemon: dict[str, Any] = cache["pokemon"]
    raw_moves: dict[str, Any] = cache["moves"]
    raw_abilities: dict[str, Any] = cache["abilities"]
    raw_evolution_chains: dict[str, list[dict[str, Any]]] = cache["evolution_chains"]

    move_catalog = {
        move_name: _build_move(move_name, move_data)
        for move_name, move_data in raw_moves.items()
    }
    ability_object_cache: dict[str, Ability] = {}
    species_by_key: dict[str, PokemonSpecies] = {}

    # Build a fast lookup to identify stage and family from evolution chains.
    stage_lookup: dict[str, int] = {}
    family_roots: dict[str, str] = {}
    for chain in raw_evolution_chains.values():
        root = chain[0]["species"]
        for node in chain:
            stage_lookup[node["species"]] = int(node["stage"])
            family_roots[node["species"]] = root

    for key, data in raw_pokemon.items():
        stage = stage_lookup.get(key, 0)
        types = [_type_from_name(type_name) for type_name in data["types"]]
        primary_type = types[0].element
        if stage == 0 and primary_type == ElementType.GRASS:
            species_cls = GrassStarterSpecies
        elif stage == 0 and primary_type == ElementType.FIRE:
            species_cls = FireStarterSpecies
        elif stage == 0 and primary_type == ElementType.WATER:
            species_cls = WaterStarterSpecies
        else:
            species_cls = EvolutionStageSpecies

        possible_abilities = [
            _build_ability(
                ability_name=ability_entry["name"],
                is_hidden=bool(ability_entry["is_hidden"]),
                ability_details=raw_abilities,
                ability_cache=ability_object_cache,
            )
            for ability_entry in sorted(data["abilities"], key=lambda a: a["slot"])
        ]

        species = species_cls(
            name=_display_name(key),
            description=f"{_display_name(key)} species derived from cached PokeAPI data.",
            species_key=key,
            dex_number=int(data["id"]),
            generation=_generation_from_name(data["generation"]),
            types=types,
            base_stats=_stats_from_api(data["stats"]),
            possible_abilities=possible_abilities,
            learnset=_learnset_for_species(key, raw_pokemon, move_catalog),
            sprite_asset=_sprite_asset(key, project_root),
        )
        if isinstance(species, EvolutionStageSpecies):
            species.stage_index = stage + 1
        species_by_key[key] = species

    # Create evolution lines and rules from evolution-chain payloads.
    family_chains: dict[str, list[str]] = {}
    for chain in raw_evolution_chains.values():
        ordered = sorted(chain, key=lambda n: int(n["stage"]))
        ordered_keys = [
            node["species"] for node in ordered if node["species"] in species_by_key
        ]
        if not ordered_keys:
            continue
        family_chains[ordered_keys[0]] = ordered_keys

        for index in range(len(ordered_keys) - 1):
            current_key = ordered_keys[index]
            next_key = ordered_keys[index + 1]
            next_node = next(node for node in ordered if node["species"] == next_key)
            species_by_key[current_key].evolution_rules.append(
                _build_rule(next_key, next_node.get("trigger"))
            )

        line = EvolutionLine()
        for node in ordered:
            species_key = node["species"]
            if species_key not in species_by_key:
                continue
            line.add_stage(
                species=species_by_key[species_key],
                index=int(node["stage"]) + 1,
                rule=_build_rule(species_key, node.get("trigger"))
                if node.get("trigger")
                else None,
            )
        for species_key in ordered_keys:
            species_by_key[species_key].evolution_line = line

    # Family view model for left navigation.
    families: dict[str, list[PokemonSpecies]] = {}
    for root, ordered_keys in sorted(
        family_chains.items(),
        key=lambda item: species_by_key[item[0]].dex_number,
    ):
        family_name = f"{species_by_key[root].name} Family"
        families[family_name] = [species_by_key[key] for key in ordered_keys]

    leftovers = HeldItem(name="Leftovers", description="Restores HP each turn.")
    charcoal = HeldItem(name="Charcoal", description="Boosts Fire move power.")
    mystic_water = HeldItem(name="Mystic Water", description="Boosts Water move power.")

    def first_ability(species: PokemonSpecies) -> Ability | None:
        return species.possible_abilities[0] if species.possible_abilities else None

    bulbasaur = species_by_key["bulbasaur"]
    charmander = species_by_key["charmander"]
    squirtle = species_by_key["squirtle"]
    charizard = species_by_key["charizard"]

    instances: list[PokemonInstance] = [
        _starter_instance_class(bulbasaur.types[0].element)(
            name="Buddy",
            nickname="Buddy",
            species=bulbasaur,
            level=17,
            current_hp=45,
            chosen_ability=first_ability(bulbasaur),
            held_item=leftovers,
            move_slots=_instance_moves(bulbasaur, 17),
            identity=PokemonIdentity(
                trainer_id=17233, secret_id=44122, personality_value=0xA5D31C77
            ),
            nature=NATURES["Modest"],
        ),
        _starter_instance_class(charmander.types[0].element)(
            name="Blaze",
            nickname="Blaze",
            species=charmander,
            level=19,
            current_hp=44,
            chosen_ability=first_ability(charmander),
            held_item=charcoal,
            move_slots=_instance_moves(charmander, 19),
            identity=PokemonIdentity(
                trainer_id=17233, secret_id=44122, personality_value=0xF1201E2A
            ),
            nature=NATURES["Adamant"],
            status=BurnStatus(),
        ),
        _starter_instance_class(squirtle.types[0].element)(
            name="Shellshock",
            nickname="Shellshock",
            species=squirtle,
            level=20,
            current_hp=50,
            chosen_ability=first_ability(squirtle),
            held_item=mystic_water,
            move_slots=_instance_moves(squirtle, 20),
            identity=PokemonIdentity(
                trainer_id=17233, secret_id=44122, personality_value=0x0A1012FF
            ),
            nature=NATURES["Bold"],
        ),
        BattleReadyPokemon(
            name="Apex",
            nickname="Apex",
            species=charizard,
            level=50,
            current_hp=140,
            chosen_ability=first_ability(charizard),
            held_item=charcoal,
            move_slots=_instance_moves(charizard, 50),
            identity=PokemonIdentity(
                trainer_id=9012, secret_id=60001, personality_value=0x4A4A0101
            ),
            nature=NATURES["Timid"],
        ),
    ]

    default_trainer = Trainer(
        name="Red",
        description="A seasoned starter trainer from Pallet Town.",
        identity=TrainerIdentity(trainer_id=17233, secret_id=44122, display_name="Red"),
        badges=3,
        home_town="Pallet Town",
        sprite_asset=_sprite_asset("red", project_root),
    )
    veteran_trainer = Trainer(
        name="Champion Steven",
        description="Hoenn's Champion; inherited Apex for competitive play.",
        identity=TrainerIdentity(
            trainer_id=9012, secret_id=60001, display_name="Steven"
        ),
        badges=8,
        home_town="Mossdeep City",
        sprite_asset=_sprite_asset("steven", project_root),
    )
    for pokemon in instances[:3]:
        default_trainer.add_to_party(pokemon)
    veteran_trainer.add_to_party(instances[3])

    trainers = [default_trainer, veteran_trainer]

    return DomainCatalog(
        species_by_key=species_by_key,
        families=families,
        instances=instances,
        trainers=trainers,
    )
