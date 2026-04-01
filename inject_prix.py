#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Injecte les prix depuis prix-export.json dans HARDCODED_DEFAULT_PRICES de chaque page HTML."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPORT_FILE = ROOT / "prix-export.json"

STORAGE_KEY_TO_FILE = {
    "pacotille-default-prices": "test_pacotille.html",
    "verroterie-default-prices": "verroterie.html",
    "campagne-default-prices": "campagne.html",
    "ultra-vintage-default-prices": "ultra-vintage.html",
    "the-ou-cafe-default-prices": "the-ou-cafe.html",
    "lampes-default-prices": "lampes.html",
    "cabinet-de-curiosite-default-prices": "cabinet-de-curiosite.html",
    "tableaux-default-prices": "tableaux.html",
}


def js_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def format_price(v) -> str:
    if isinstance(v, (int, float)):
        return f"{float(v):.2f}"
    s = str(v).strip()
    if not s:
        return ""
    try:
        return f"{float(s.replace(',', '.')):.2f}"
    except ValueError:
        return s


def to_js_object_literal(prices: dict) -> str:
    if not prices:
        return "{}"
    lines = []
    for k in sorted(prices.keys()):
        v = prices[k]
        if v is None or v == "":
            continue
        val = format_price(v)
        if not val:
            continue
        lines.append(f"      '{js_escape(k)}': '{js_escape(val)}'")
    if not lines:
        return "{}"
    return "{\n" + ",\n".join(lines) + "\n    }"


def replace_hardcoded_block(html: str, js_obj: str) -> str:
    """Remplace const HARDCODED_DEFAULT_PRICES = ... ; par le nouvel objet."""
    replacement = f"    const HARDCODED_DEFAULT_PRICES = {js_obj};\n"
    # Cas déjà injecté (multiligne) ou {}
    pattern = re.compile(
        r"    const HARDCODED_DEFAULT_PRICES = \{[\s\S]*?\n    \};",
        re.MULTILINE,
    )
    if pattern.search(html):
        return pattern.sub(replacement.rstrip("\n"), html, count=1)
    # Cas une seule ligne vide {}
    if "const HARDCODED_DEFAULT_PRICES = {};" in html:
        return html.replace(
            "const HARDCODED_DEFAULT_PRICES = {};",
            f"const HARDCODED_DEFAULT_PRICES = {js_obj};",
            1,
        )
    raise ValueError("Bloc HARDCODED_DEFAULT_PRICES introuvable dans ce fichier.")


def main():
    if not EXPORT_FILE.is_file():
        print(f"Fichier manquant : {EXPORT_FILE}")
        print("Crée prix-export.json avec le JSON exporté depuis le navigateur.")
        return 1

    raw = EXPORT_FILE.read_text(encoding="utf-8").strip()
    if not raw or raw == "{}":
        print("prix-export.json est vide.")
        print(f"Lis les instructions dans : {ROOT / 'extraire-prix-console.txt'}")
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print("JSON invalide dans prix-export.json :", e)
        return 1

    if not isinstance(data, dict):
        print("Le JSON racine doit être un objet { ... }.")
        return 1

    updated = 0
    for storage_key, rel_path in STORAGE_KEY_TO_FILE.items():
        if storage_key not in data:
            continue
        prices = data[storage_key]
        if not isinstance(prices, dict):
            print(f"Ignoré (pas un objet) : {storage_key}")
            continue

        path = ROOT / rel_path
        if not path.is_file():
            print(f"Fichier absent : {path}")
            continue

        html = path.read_text(encoding="utf-8")
        js_obj = to_js_object_literal(prices)
        try:
            new_html = replace_hardcoded_block(html, js_obj)
        except ValueError as e:
            print(f"{rel_path}: {e}")
            continue

        path.write_text(new_html, encoding="utf-8")
        print(f"OK — {rel_path} ({len([k for k, v in prices.items() if v not in (None, '')])} prix)")
        updated += 1

    if updated == 0:
        print(
            "Aucune clé reconnue (ex. pacotille-default-prices) dans prix-export.json.\n"
            "Le JSON doit ressembler à :\n"
            '  { "campagne-default-prices": { "image catégories/...": "12.50" }, ... }'
        )
        return 1

    print(f"\nTerminé : {updated} fichier(s) mis à jour. Puis : git add && git commit && git push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
