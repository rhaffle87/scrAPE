# -*- coding: utf-8 -*-
"""
Generates comprehensive multilingual dictionary data for docs/site/i18n.js
Covers all 55 sections, 65 card titles, 32 code block headers, 10 alert callouts,
subheadings, code snippet comments, table headers, and the full footer.
"""
import json
import os

with open('docs/site/sections_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print(f"Loaded {len(manifest)} sections from manifest.")
