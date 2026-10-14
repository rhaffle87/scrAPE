# -*- coding: utf-8 -*-
"""
Master Compiler for docs/site/i18n.js
"""

import json
import os
import sys

sys.path.append('scripts')
from generate_i18n_data import UI_TRANSLATIONS, MODULE_TRANSLATIONS, FOOTER_TRANSLATIONS
from sections_multilingual_db import SECTIONS_DB
from snippets_and_maps import SNIPPETS, LISTS, H3_MAP, TH_MAP

with open('docs/site/existing_i18n.json', 'r', encoding='utf-8') as f:
    existing_i18n = json.load(f)

LANGS = ['en', 'id', 'zh', 'es', 'ja', 'ru', 'de']

print("Building unified I18N_DICTS object...")
unified_dicts = {}

for lang in LANGS:
    d = {}
    # Meta
    d["meta"] = existing_i18n[lang]["meta"]
    # UI
    d["ui"] = UI_TRANSLATIONS[lang]
    # Modules
    d["modules"] = MODULE_TRANSLATIONS[lang]
    # Nav
    d["nav"] = existing_i18n[lang]["nav"]
    # Footer
    d["footer"] = FOOTER_TRANSLATIONS[lang]
    # Sections
    d["sections"] = {}
    for sec_id, sec_data in SECTIONS_DB.items():
        d["sections"][sec_id] = sec_data[lang]
    # Snippets
    if lang in SNIPPETS:
        d["snippets"] = SNIPPETS[lang]
    # Lists
    if lang in LISTS:
        d["lists"] = LISTS[lang]
    # H3 Map
    if lang in H3_MAP:
        d["h3Map"] = H3_MAP[lang]
    # TH Map
    if lang in TH_MAP:
        d["thMap"] = TH_MAP[lang]

    unified_dicts[lang] = d

print(f"Constructed dictionaries for {len(unified_dicts)} languages.")

# Now generate JavaScript source code
js_code = """/**
 * scrAPE v0.30.1 — Technical Documentation Portal
 * Tactical Multilingual Internationalization (i18n) Engine
 * Supported Languages: English (EN), Indonesian (ID), Chinese (ZH), Spanish (ES), Japanese (JA), Russian (RU), German (DE)
 */

const I18N_DICTS = """ + json.dumps(unified_dicts, indent=2, ensure_ascii=False) + """;

/**
 * Applies the selected language to the portal DOM dynamically.
 * @param {string} lang Target language code ('en', 'id', 'zh', 'es', 'ja', 'ru', 'de')
 */
function setPortalLanguage(lang) {
  if (!I18N_DICTS[lang]) {
    lang = 'en';
  }
  const dict = I18N_DICTS[lang];

  // 1. Update HTML document attributes & metadata
  document.documentElement.lang = lang;
  if (dict.meta) {
    if (dict.meta.title) document.title = dict.meta.title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && dict.meta.desc) metaDesc.setAttribute('content', dict.meta.desc);
  }

  // 2. Update Search Placeholder & Header Link
  const searchInput = document.getElementById('search-input');
  if (searchInput && dict.ui.searchPlaceholder) {
    searchInput.placeholder = dict.ui.searchPlaceholder;
  }
  const ghLink = document.querySelector('.header-links a[href*="github.com"]');
  if (ghLink && dict.ui.githubLink) {
    ghLink.textContent = dict.ui.githubLink;
  }

  // 3. Update Module Headings in Sidebar
  const moduleTitles = document.querySelectorAll('.nav-module-title');
  moduleTitles.forEach((modTitle, idx) => {
    if (dict.modules && dict.modules[idx]) {
      const span = modTitle.querySelector('span:first-child');
      if (span) span.textContent = dict.modules[idx];
    }
  });

  // 4. Update Navigation Sub-Links
  const navLinks = document.querySelectorAll('.nav-sub-item a');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href) {
      const cleanHash = href.replace('#', '');
      if (dict.nav && dict.nav[cleanHash]) {
        // preserve badge if present
        const hasBadge = link.querySelector('.badge-new') || link.querySelector('.badge-tag');
        const badgeHtml = hasBadge ? hasBadge.outerHTML : '';
        link.textContent = dict.nav[cleanHash];
        if (badgeHtml) {
          link.insertAdjacentHTML('beforeend', ' ' + badgeHtml);
        }
      }
    }
  });

  // 5. Update All 55 Sections (Tag, H1, Desc, Card Titles, Code Headers, Alerts)
  if (dict.sections) {
    Object.keys(dict.sections).forEach(secId => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const secData = dict.sections[secId];
        const tagEl = secEl.querySelector('.section-tag');
        const h1El = secEl.querySelector('.section-header h1');
        const descEl = secEl.querySelector('.section-desc');

        if (tagEl && secData.tag) tagEl.textContent = secData.tag;
        if (h1El && secData.h1) h1El.textContent = secData.h1;
        if (descEl && secData.desc) descEl.textContent = secData.desc;

        // Card Titles inside section
        if (secData.cards && Array.isArray(secData.cards)) {
          const cardTitleEls = secEl.querySelectorAll('.card-title');
          secData.cards.forEach((title, idx) => {
            if (cardTitleEls[idx]) {
              cardTitleEls[idx].textContent = title;
            }
          });
        }

        // Code block headers inside section
        if (secData.codeHeaders && Array.isArray(secData.codeHeaders)) {
          const codeHeaderSpans = secEl.querySelectorAll('.code-header span:first-child');
          secData.codeHeaders.forEach((chText, idx) => {
            if (codeHeaderSpans[idx]) {
              codeHeaderSpans[idx].textContent = chText;
            }
          });
        }

        // Alert callouts inside section
        if (secData.alerts && Array.isArray(secData.alerts)) {
          const alertEls = secEl.querySelectorAll('.alert');
          secData.alerts.forEach((altData, idx) => {
            const aEl = alertEls[idx];
            if (aEl) {
              const aTitle = aEl.querySelector('.alert-title');
              if (aTitle && altData.title) {
                aTitle.textContent = altData.title;
              }
              if (altData.bodyHtml) {
                const titleHtml = aTitle ? aTitle.outerHTML : '';
                aEl.innerHTML = titleHtml + ' ' + altData.bodyHtml;
              }
            }
          });
        }
      }
    });
  }

  // 6. Update Code Snippet Comments (e.g. bash # comments)
  if (dict.snippets) {
    Object.keys(dict.snippets).forEach(secId => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const preEl = secEl.querySelector('pre');
        if (preEl && dict.snippets[secId]) {
          preEl.textContent = dict.snippets[secId];
        }
      }
    });
  }

  // 7. Update Section Lists (Wizard Options, BFS Steps)
  if (dict.lists) {
    Object.keys(dict.lists).forEach(secId => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const listItems = secEl.querySelectorAll('ol > li, ul > li');
        const translations = dict.lists[secId];
        if (translations && Array.isArray(translations)) {
          translations.forEach((itemHtml, idx) => {
            if (listItems[idx]) {
              listItems[idx].innerHTML = itemHtml;
            }
          });
        }
      }
    });
  }

  // 8. Update Subheadings inside Cards (h3 / h4)
  document.querySelectorAll('.card h3, .card h4').forEach(h => {
    if (!h.dataset.origText) h.dataset.origText = h.textContent.trim();
    const orig = h.dataset.origText;
    if (dict.h3Map && dict.h3Map[orig]) {
      h.textContent = dict.h3Map[orig];
    } else if (lang === 'en') {
      h.textContent = orig;
    }
  });

  // 9. Update Table Headers (th)
  document.querySelectorAll('th').forEach(th => {
    if (!th.dataset.origText) th.dataset.origText = th.textContent.trim();
    const orig = th.dataset.origText;
    if (dict.thMap && dict.thMap[orig]) {
      th.textContent = dict.thMap[orig];
    } else if (lang === 'en') {
      th.textContent = orig;
    }
  });

  // 10. Update Entire Footer
  if (dict.footer) {
    const fLogo = document.querySelector('.footer-logo');
    if (fLogo && dict.footer.logo) fLogo.textContent = dict.footer.logo;

    const fTagline = document.querySelector('.footer-tagline');
    if (fTagline && dict.footer.tagline) fTagline.textContent = dict.footer.tagline;

    if (dict.footer.badges) {
      const badgeEls = document.querySelectorAll('.footer-badges .badge-tag');
      dict.footer.badges.forEach((bText, idx) => {
        if (badgeEls[idx]) badgeEls[idx].textContent = bText;
      });
    }

    if (dict.footer.headings) {
      const headingEls = document.querySelectorAll('.footer-nav-col .footer-heading');
      if (headingEls[0] && dict.footer.headings.repo) headingEls[0].textContent = dict.footer.headings.repo;
      if (headingEls[1] && dict.footer.headings.docs) headingEls[1].textContent = dict.footer.headings.docs;
    }

    if (dict.footer.links && Array.isArray(dict.footer.links)) {
      const linkEls = document.querySelectorAll('.footer-nav-col .footer-link-list a');
      dict.footer.links.forEach((lText, idx) => {
        if (linkEls[idx]) linkEls[idx].textContent = lText;
      });
    }

    const fCopy = document.querySelector('.footer-copy');
    if (fCopy && dict.footer.copy) fCopy.textContent = dict.footer.copy;

    const fSysinfo = document.querySelector('.footer-sysinfo');
    if (fSysinfo && dict.footer.sysinfo) fSysinfo.textContent = dict.footer.sysinfo;
  }

  // 11. Update Interactive CLI Builder UI Labels
  const builderTitle = document.querySelector('#sec-cli-builder .card-title');
  if (builderTitle && dict.ui.commandBuilder) {
    builderTitle.textContent = dict.ui.commandBuilder;
  }
  const builderOutputLabel = document.querySelector('#sec-cli-builder .code-header span');
  if (builderOutputLabel && dict.ui.builderOutputLabel) {
    builderOutputLabel.textContent = dict.ui.builderOutputLabel;
  }

  // 12. Copy Buttons
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(btn => {
    if (dict.ui.copyCode && !btn.textContent.includes('!')) {
      btn.textContent = dict.ui.copyCode;
    }
  });

  // 13. Sync Unified Language Picker
  const currentCodeEl = document.getElementById('current-lang-code');
  if (currentCodeEl) {
    currentCodeEl.textContent = lang.toUpperCase();
  }

  document.querySelectorAll('.lang-choice').forEach(choice => {
    if (choice.getAttribute('data-lang') === lang) {
      choice.classList.add('active');
    } else {
      choice.classList.remove('active');
    }
  });

  // 14. Persist Choice
  try {
    localStorage.setItem('scrape_doc_lang', lang);
    const url = new URL(window.location.href);
    if (url.searchParams.get('lang') !== lang) {
      url.searchParams.set('lang', lang);
      window.history.replaceState({}, '', url.toString());
    }
  } catch (e) {
    // Ignore local file restrictions
  }

  window.I18N_CURRENT_DICT = dict;
  window.I18N_CURRENT_LANG = lang;
  document.dispatchEvent(new CustomEvent('languagechange', { detail: { lang, dict } }));
}

/**
 * Initializes language listeners on page ready.
 */
function initPortalI18n() {
  let activeLang = 'en';

  // Check URL parameter first
  try {
    const url = new URL(window.location.href);
    const param = url.searchParams.get('lang');
    if (param && I18N_DICTS[param]) {
      activeLang = param;
    } else {
      const stored = localStorage.getItem('scrape_doc_lang');
      if (stored && I18N_DICTS[stored]) {
        activeLang = stored;
      } else {
        const browser = (navigator.language || '').slice(0, 2).toLowerCase();
        if (I18N_DICTS[browser]) {
          activeLang = browser;
        }
      }
    }
  } catch (e) {
    // Fallback to default
  }

  // Unified Language Picker Trigger & Panel
  const pickerContainer = document.getElementById('lang-picker-container');
  const pickerBtn = document.getElementById('lang-picker-btn');
  const dropdownPanel = document.getElementById('lang-dropdown-panel');

  if (pickerContainer && pickerBtn && dropdownPanel) {
    pickerBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isClosed = dropdownPanel.style.display === 'none';
      if (isClosed) {
        dropdownPanel.style.display = 'flex';
        pickerContainer.classList.add('open');
        pickerBtn.setAttribute('aria-expanded', 'true');
      } else {
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!pickerContainer.contains(e.target)) {
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && dropdownPanel.style.display !== 'none') {
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
        pickerBtn.focus();
      }
    });

    // Language item selection
    document.querySelectorAll('.lang-choice').forEach(choice => {
      choice.addEventListener('click', () => {
        const lang = choice.getAttribute('data-lang');
        setPortalLanguage(lang);
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Initial Language Render
  setPortalLanguage(activeLang);
}

// Hook into DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPortalI18n);
} else {
  initPortalI18n();
}
"""

with open('docs/site/i18n.js', 'w', encoding='utf-8') as f:
    f.write(js_code)

print("Generated docs/site/i18n.js successfully! File size:", len(js_code), "bytes")
