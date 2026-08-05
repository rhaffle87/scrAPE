document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSearch();
  initCliBuilder();
  initCopyButtons();
});

/* Navigation Router */
function initNavigation() {
  const moduleTitles = document.querySelectorAll('.nav-module-title');
  const subLinks = document.querySelectorAll('.nav-sub-item a');
  const docSections = document.querySelectorAll('.doc-section');

  // Toggle Module Accordions
  moduleTitles.forEach(title => {
    title.addEventListener('click', () => {
      const group = title.parentElement;
      const isAlreadyActive = group.classList.contains('active');
      
      // Keep only one active or toggle current
      document.querySelectorAll('.nav-module-group').forEach(g => g.classList.remove('active'));
      if (!isAlreadyActive) {
        group.classList.add('active');
      }
    });
  });

  // Switch Sub-Sections
  subLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href').replace('#', '');
      
      // Update sub-item active state
      document.querySelectorAll('.nav-sub-item').forEach(item => item.classList.remove('active'));
      link.parentElement.classList.add('active');

      // Update active module group
      const parentGroup = link.closest('.nav-module-group');
      if (parentGroup) {
        document.querySelectorAll('.nav-module-group').forEach(g => g.classList.remove('active'));
        parentGroup.classList.add('active');
      }

      // Display Target Doc Section
      docSections.forEach(section => {
        section.classList.remove('active');
        if (section.id === targetId) {
          section.classList.add('active');
        }
      });

      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
}

/* Client-Side Live Search Engine */
function initSearch() {
  const searchInput = document.getElementById('doc-search');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    const docSections = document.querySelectorAll('.doc-section');
    const cards = document.querySelectorAll('.card');

    if (!query) {
      // Clear Highlights & Reset Sections
      cards.forEach(card => {
        card.style.display = 'block';
      });
      return;
    }

    cards.forEach(card => {
      const text = card.innerText.toLowerCase();
      if (text.includes(query)) {
        card.style.display = 'block';
        // Make parent section visible if hidden
        const parentSection = card.closest('.doc-section');
        if (parentSection && !parentSection.classList.contains('active')) {
          docSections.forEach(s => s.classList.remove('active'));
          parentSection.classList.add('active');
        }
      } else {
        card.style.display = 'none';
      }
    });
  });
}

/* Interactive CLI Command Builder */
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

/* Clipboard Copy Utility */
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
          showToast('COMMAND COPIED TO CLIPBOARD');
        }).catch(err => {
          console.error('Copy failed', err);
        });
      }
    });
  });
}

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
  }, 2500);
}
