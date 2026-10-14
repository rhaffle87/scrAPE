# -*- coding: utf-8 -*-
"""
Build Complete Catalog for scrAPE Multilingual Documentation
Generates the complete i18n dictionary for en, id, zh, es, ja, ru, de
"""
import json
import os
import re

with open('docs/site/existing_i18n.json', 'r', encoding='utf-8') as f:
    existing = json.load(f)

with open('docs/site/sections_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print(f"Loaded existing i18n with {len(existing)} languages.")
