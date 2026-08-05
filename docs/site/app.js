document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSearch();
  initCliBuilder();
  initCopyButtons();
  initScrollToTop();
  initHamburgerMenu();
  handleHashRoute();
});

/* ── Navigation Router ──────────────────────────────────────────────────── */
function initNavigation() {
  const moduleTitles = document.querySelectorAll('.nav-module-title');
  const subLinks = document.querySelectorAll('.nav-sub-item a');

  moduleTitles.forEach(title => {
    title.addEventListener('click', () => {
      const group = title.parentElement;
      const isAlreadyActive = group.classList.contains('active');
      document.querySelectorAll('.nav-module-group').forEach(g => g.classList.remove('active'));
      if (!isAlreadyActive) {
        group.classList.add('active');
      }
    });
  });

  subLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href').replace('#', '');
      navigateToSection(targetId);
      history.pushState(null, '', '#' + targetId);
      closeMobileSidebar();
    });
  });
}

function navigateToSection(targetId) {
  const docSections = document.querySelectorAll('.doc-section');
  const subItems = document.querySelectorAll('.nav-sub-item');

  subItems.forEach(item => item.classList.remove('active'));
  docSections.forEach(section => section.classList.remove('active'));

  const targetSection = document.getElementById(targetId);
  if (targetSection) {
    targetSection.classList.add('active');
  }

  const matchingLink = document.querySelector(`.nav-sub-item a[href="#${targetId}"]`);
  if (matchingLink) {
    matchingLink.parentElement.classList.add('active');
    const parentGroup = matchingLink.closest('.nav-module-group');
    if (parentGroup) {
      document.querySelectorAll('.nav-module-group').forEach(g => g.classList.remove('active'));
      parentGroup.classList.add('active');
    }
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleHashRoute() {
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    navigateToSection(hash);
  }
}

window.addEventListener('hashchange', () => {
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    navigateToSection(hash);
  }
});

/* ── Client-Side Live Search Engine ─────────────────────────────────────── */
function initSearch() {
  const searchInput = document.getElementById('doc-search');
  if (!searchInput) return;

  // Keyboard shortcut: Ctrl+K or / to focus search
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.value = '';
      searchInput.dispatchEvent(new Event('input'));
      searchInput.blur();
    }
  });

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    const docSections = document.querySelectorAll('.doc-section');
    const cards = document.querySelectorAll('.card');
    const resultCounter = document.getElementById('search-result-count');

    // Clear any existing highlights
    document.querySelectorAll('mark.search-highlight').forEach(mark => {
      const parent = mark.parentNode;
      parent.replaceChild(document.createTextNode(mark.textContent), mark);
      parent.normalize();
    });

    if (!query) {
      cards.forEach(card => { card.style.display = 'block'; });
      if (resultCounter) resultCounter.textContent = '';
      return;
    }

    let matchCount = 0;
    let firstMatchSection = null;

    cards.forEach(card => {
      const text = card.innerText.toLowerCase();
      if (text.includes(query)) {
        card.style.display = 'block';
        matchCount++;
        const parentSection = card.closest('.doc-section');
        if (!firstMatchSection && parentSection) {
          firstMatchSection = parentSection;
        }
      } else {
        card.style.display = 'none';
      }
    });

    if (firstMatchSection) {
      docSections.forEach(s => s.classList.remove('active'));
      firstMatchSection.classList.add('active');

      // Also expand the parent nav module
      const sectionId = firstMatchSection.id;
      const matchingLink = document.querySelector(`.nav-sub-item a[href="#${sectionId}"]`);
      if (matchingLink) {
        const parentGroup = matchingLink.closest('.nav-module-group');
        if (parentGroup) {
          document.querySelectorAll('.nav-module-group').forEach(g => g.classList.remove('active'));
          parentGroup.classList.add('active');
        }
      }
    }

    if (resultCounter) {
      resultCounter.textContent = matchCount > 0 ? matchCount + ' found' : 'no results';
    }
  });
}

/* ── Interactive CLI Command Builder ────────────────────────────────────── */
function initCliBuilder() {
  const inputs = [
    'cli-keyword', 'cli-seed', 'cli-max-results', 'cli-workers',
    'cli-dl-workers', 'cli-page-limit', 'cli-crawl-depth', 'cli-save-rejected'
  ];

  const checkboxes = [
    'cli-download-media', 'cli-use-state-cache', 'cli-strict-domain',
    'cli-ignore-robots', 'cli-skip-search', 'cli-clear-cache'
  ];

  function updateCommand() {
    let cmd = 'python src/cli/main.py';

    const keyword = document.getElementById('cli-keyword')?.value.trim();
    const seed = document.getElementById('cli-seed')?.value.trim();
    const maxResults = document.getElementById('cli-max-results')?.value.trim();
    const workers = document.getElementById('cli-workers')?.value.trim();
    const dlWorkers = document.getElementById('cli-dl-workers')?.value.trim();
    const pageLimit = document.getElementById('cli-page-limit')?.value.trim();
    const crawlDepth = document.getElementById('cli-crawl-depth')?.value.trim();
    const saveRejected = document.getElementById('cli-save-rejected')?.value.trim();

    if (keyword) cmd += ` --keyword "${keyword}"`;
    if (seed) cmd += ` --seed "${seed}"`;
    if (maxResults && maxResults !== '50') cmd += ` --max-results ${maxResults}`;
    if (workers && workers !== '6') cmd += ` --workers ${workers}`;
    if (dlWorkers && dlWorkers !== '16') cmd += ` --dl-workers ${dlWorkers}`;
    if (pageLimit && pageLimit !== '100') cmd += ` --page-limit ${pageLimit}`;
    if (crawlDepth && crawlDepth !== '2') cmd += ` --crawl-depth ${crawlDepth}`;
    if (saveRejected) cmd += ` --save-rejected "${saveRejected}"`;

    checkboxes.forEach(id => {
      const cb = document.getElementById(id);
      if (cb?.checked) {
        const flagName = id.replace('cli-', '');
        cmd += ` --${flagName}`;
      }
    });

    const outputElement = document.getElementById('generated-cli-output');
    if (outputElement) {
      outputElement.textContent = cmd;
    }
  }

  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateCommand);
  });

  checkboxes.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', updateCommand);
  });

  updateCommand();
}

/* ── Clipboard Copy Utility ─────────────────────────────────────────────── */
function initCopyButtons() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      let textToCopy = '';

      if (targetId) {
        const targetEl = document.getElementById(targetId);
        if (targetEl) textToCopy = targetEl.textContent;
      } else {
        const container = btn.closest('.code-block-container');
        if (container) {
          const pre = container.querySelector('pre');
          if (pre) textToCopy = pre.textContent;
        }
      }

      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy.trim()).then(() => {
          showToast('COPIED TO CLIPBOARD');
        }).catch(err => {
          console.error('Copy failed', err);
        });
      }
    });
  });
}

/* ── Scroll-to-Top Button ───────────────────────────────────────────────── */
function initScrollToTop() {
  const btn = document.getElementById('scroll-top-btn');
  if (!btn) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ── Mobile Hamburger Menu ──────────────────────────────────────────────── */
function initHamburgerMenu() {
  const btn = document.getElementById('hamburger-btn');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (!btn || !sidebar) return;

  btn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      closeMobileSidebar();
    });
  }
}

function closeMobileSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('active');
}

/* ── Toast ───────────────────────────────────────────────────────────────── */
function showToast(message) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 2200);
}
