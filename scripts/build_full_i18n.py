# -*- coding: utf-8 -*-
"""
Full i18n Builder for scrAPE Documentation Portal
Builds complete translation dictionaries for:
en, id, zh, es, ja, ru, de
"""

import json
import os
import sys

# 1. Base Metadata and UI Labels
from generate_i18n_data import UI_TRANSLATIONS, MODULE_TRANSLATIONS, FOOTER_TRANSLATIONS

print("Imported UI, Modules, and Footer.")
