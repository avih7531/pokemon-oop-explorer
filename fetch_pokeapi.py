"""Incremental PokeAPI fetcher — dumps to pokeapi_cache.json after every call."""

import json
import urllib.request
import time
import argparse
from pathlib import Path

CACHE_FILE = Path("pokeapi_cache.json")

SPECIES_KEYS = [
    "bulbasaur",
    "ivysaur",
    "venusaur",
    "charmander",
    "charmeleon",
    "charizard",
    "squirtle",
    "wartortle",
    "blastoise",
    "chikorita",
    "bayleef",
    "meganium",
    "cyndaquil",
    "quilava",
    "typhlosion",
    "totodile",
    "croconaw",
    "feraligatr",
    "treecko",
    "grovyle",
    "sceptile",
    "torchic",
    "combusken",
    "blaziken",
    "mudkip",
    "marshtomp",
    "swampert",
]

VERSION_GROUP = "ruby-sapphire"


def log(message: str) -> None:
    print(message, flush=True)


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {
        "pokemon": {},
        "moves": {},
        "abilities": {},
        "evolution_chains": {},
        "meta": {"api_calls": 0, "last_call_url": None, "history": []},
    }


def save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def fetch_json(url: str, label: str, cache: dict, delay: float) -> dict:
    log(f"  GET {label}: {url}")
    req = urllib.request.Request(
        url, headers={"User-Agent": "pokemon-oop-explorer/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())

    # Persist immediately after each API call (even before higher-level processing).
    meta = cache.setdefault(
        "meta", {"api_calls": 0, "last_call_url": None, "history": []}
    )
    meta["api_calls"] = int(meta.get("api_calls", 0)) + 1
    meta["last_call_url"] = url
    history = meta.setdefault("history", [])
    history.append({"label": label, "url": url})
    # Keep history bounded.
    if len(history) > 500:
        del history[:-500]
    save_cache(cache)

    if delay > 0:
        time.sleep(delay)
    return data


def fetch_pokemon(name: str, cache: dict, delay: float) -> None:
    """Fetch /pokemon/{name} and /pokemon-species/{name}, store combined result."""
    if name in cache["pokemon"] and cache["pokemon"][name].get("_complete"):
        log(f"[SKIP] {name} already cached")
        return

    data = fetch_json(
        f"https://pokeapi.co/api/v2/pokemon/{name}", f"pokemon/{name}", cache, delay
    )

    stats = {}
    for s in data["stats"]:
        stats[s["stat"]["name"]] = s["base_stat"]

    types = [t["type"]["name"] for t in sorted(data["types"], key=lambda x: x["slot"])]

    abilities = []
    for a in data["abilities"]:
        abilities.append(
            {
                "name": a["ability"]["name"],
                "is_hidden": a["is_hidden"],
                "slot": a["slot"],
            }
        )

    level_up_moves = []
    for m in data["moves"]:
        for vgd in m["version_group_details"]:
            if (
                vgd["version_group"]["name"] == VERSION_GROUP
                and vgd["move_learn_method"]["name"] == "level-up"
            ):
                level_up_moves.append(
                    {
                        "name": m["move"]["name"],
                        "level": vgd["level_learned_at"],
                    }
                )
    level_up_moves.sort(key=lambda x: (x["level"], x["name"]))

    sp = fetch_json(
        f"https://pokeapi.co/api/v2/pokemon-species/{name}",
        f"species/{name}",
        cache,
        delay,
    )

    cache["pokemon"][name] = {
        "id": data["id"],
        "types": types,
        "stats": stats,
        "abilities": abilities,
        "level_up_moves": level_up_moves,
        "generation": sp["generation"]["name"],
        "evo_chain_url": sp["evolution_chain"]["url"],
        "_complete": True,
    }
    save_cache(cache)
    log(f"  [OK] {name}: types={types}, stats={stats}")


def fetch_evolution_chain(url: str, cache: dict, delay: float) -> None:
    if url in cache["evolution_chains"]:
        log(f"[SKIP] evo chain {url} already cached")
        return

    data = fetch_json(url, "evo-chain", cache, delay)

    stages: list[dict] = []

    def walk(node: dict, depth: int = 0) -> None:
        species_name = node["species"]["name"]
        trigger = None
        if node.get("evolution_details"):
            ed = node["evolution_details"][0]
            trigger = {
                "trigger": ed["trigger"]["name"],
                "min_level": ed.get("min_level"),
                "item": ed["item"]["name"] if ed.get("item") else None,
                "min_happiness": ed.get("min_happiness"),
                "held_item": ed["held_item"]["name"] if ed.get("held_item") else None,
                "time_of_day": ed.get("time_of_day") or None,
            }
        stages.append({"species": species_name, "stage": depth, "trigger": trigger})
        for child in node.get("evolves_to", []):
            walk(child, depth + 1)

    walk(data["chain"])
    cache["evolution_chains"][url] = stages
    save_cache(cache)
    log(f"  [OK] evo chain: {[s['species'] for s in stages]}")


def fetch_move(name: str, cache: dict, delay: float) -> None:
    if name in cache["moves"]:
        return

    data = fetch_json(
        f"https://pokeapi.co/api/v2/move/{name}", f"move/{name}", cache, delay
    )

    cache["moves"][name] = {
        "power": data["power"],
        "accuracy": data["accuracy"],
        "pp": data["pp"],
        "type": data["type"]["name"],
        "damage_class": data["damage_class"]["name"],
    }
    save_cache(cache)
    log(
        f"  [OK] move {name}: power={data['power']} type={data['type']['name']} class={data['damage_class']['name']}"
    )


def fetch_ability(name: str, cache: dict, delay: float) -> None:
    if name in cache["abilities"]:
        return

    data = fetch_json(
        f"https://pokeapi.co/api/v2/ability/{name}", f"ability/{name}", cache, delay
    )

    effect = ""
    for e in data["effect_entries"]:
        if e["language"]["name"] == "en":
            effect = e["short_effect"]
            break

    cache["abilities"][name] = {"effect": effect}
    save_cache(cache)
    log(f"  [OK] ability {name}: {effect[:60]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Gen-3-standard starter data from PokeAPI with incremental cache."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to sleep after each API call (default: 0.5).",
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Only process first N species (0 = all)."
    )
    args = parser.parse_args()

    cache = load_cache()
    keys = SPECIES_KEYS[: args.limit] if args.limit > 0 else SPECIES_KEYS

    # Phase 1: all pokemon + species data (2 calls each, 54 total max)
    log("=== PHASE 1: Pokemon + Species data ===")
    for name in keys:
        fetch_pokemon(name, cache, args.delay)

    # Phase 2: evolution chains (deduplicated — only 9 unique chains)
    log("\n=== PHASE 2: Evolution chains ===")
    seen_urls: set[str] = set()
    for name in keys:
        url = cache["pokemon"][name]["evo_chain_url"]
        if url not in seen_urls:
            seen_urls.add(url)
            fetch_evolution_chain(url, cache, args.delay)

    # Phase 3: unique moves across all pokemon (deduplicated)
    log("\n=== PHASE 3: Move details ===")
    all_move_names: set[str] = set()
    for name in keys:
        for m in cache["pokemon"][name]["level_up_moves"]:
            all_move_names.add(m["name"])
    log(f"  {len(all_move_names)} unique level-up moves to fetch")
    for move_name in sorted(all_move_names):
        fetch_move(move_name, cache, args.delay)

    # Phase 4: unique abilities (deduplicated)
    log("\n=== PHASE 4: Ability details ===")
    all_ability_names: set[str] = set()
    for name in keys:
        for a in cache["pokemon"][name]["abilities"]:
            all_ability_names.add(a["name"])
    log(f"  {len(all_ability_names)} unique abilities to fetch")
    for ability_name in sorted(all_ability_names):
        fetch_ability(ability_name, cache, args.delay)

    log(f"\nDone. Cache at {CACHE_FILE.resolve()}")
    log(
        f"  {len(cache['pokemon'])} pokemon, {len(cache['moves'])} moves, "
        f"{len(cache['abilities'])} abilities, {len(cache['evolution_chains'])} evo chains"
    )
    log(f"  API calls made (tracked): {cache.get('meta', {}).get('api_calls', 0)}")


if __name__ == "__main__":
    main()
