# -*- coding: utf-8 -*-
"""
Constructs complete multilingual dictionaries for:
en, id, zh, es, ja, ru, de
"""
import json
import re

with open('docs/site/sections_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print(f"Total sections to localize: {len(manifest)}")
for sec_id, info in manifest.items():
    print(f"{sec_id}: h1='{info['h1']}', cards={info['cards']}, alerts={len(info['alerts'])}, code_headers={len(info['code_headers'])}")
