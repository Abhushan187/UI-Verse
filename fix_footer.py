with open('e:/nsoc26/UI-Verse/navbar.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

idx = -1
for i, line in enumerate(lines):
    if '<!-- FOOTER -->' in line or '<footer class="footer">' in line:
        idx = i
        break

if idx != -1:
    correct = '''<!-- FOOTER -->
<footer class="footer">
  <div class="footer-container">
    <div class="footer-col brand">
      <h2 class="footer-logo">⬡ UIverse</h2>
      <p>Build modern, reusable UI components with clean HTML, CSS, and JavaScript.</p>
      <div class="socials">
        <a href="https://github.com" target="_blank"><i class="fab fa-github"></i></a>
        <a href="https://linkedin.com" target="_blank"><i class="fab fa-linkedin"></i></a>
        <a href="https://twitter.com" target="_blank"><i class="fab fa-x-twitter"></i></a>
      </div>
    </div>
    <div class="footer-col">
      <h3>Explore</h3>
      <ul>
        <li><a href="button.html">Buttons</a></li>
        <li><a href="navbar.html">Navbars</a></li>
        <li><a href="cards.html">Cards</a></li>
        <li><a href="color.html">Colors</a></li>
        <li><a href="forms.html">Forms</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h3>Resources</h3>
      <ul>
        <li><a href="#">Documentation</a></li>
        <li><a href="#">GitHub Repo</a></li>
        <li><a href="#">Community</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h3>Legal</h3>
      <ul>
        <li><a href="privacypolicy.html">Privacy Policy</a></li>
        <li><a href="terms.html">Terms of Service</a></li>
      </ul>
    </div>
    <div class="footer-col newsletter">
      <h3>Stay Updated</h3>
      <p>Get notified when new components drop.</p>
      <div class="newsletter-form">
        <input type="email" placeholder="your@email.com" />
        <button type="button">Subscribe</button>
      </div>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© 2026 UIverse. Made with ❤️ for developers worldwide.</p>
  </div>
</footer>

<script src="js/features/search.js"></script>
<script src="js/features/command-palette.js"></script>

<script>
  /* ---------- Dark Mode ---------- */
  const toggle = document.getElementById('darkModeToggle');
  const icon = toggle.querySelector('i');
  if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
    icon.className = 'fa-solid fa-sun';
  }
  toggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    icon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });

  /* Sidebar */
  function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebarBackdrop').classList.toggle('visible');
  }

  /* Code Toggle */
  function toggleCode(id, btn) {
    const block = document.getElementById(id);
    const isOpen = block.classList.toggle('open');
    btn.innerHTML = isOpen
      ? '<i class="fa-solid fa-eye-slash"></i> Hide Code'
      : '<i class="fa-solid fa-code"></i> View Code';
  }

  /* Copy */
  function copyCode(id, btn) {
    navigator.clipboard.writeText(document.getElementById(id).innerText).then(() => {
      btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy';
        btn.classList.remove('copied');
      }, 2000);
    });
  }

  /* Filter */
  function filterCards(cat, btn) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.component-card').forEach(card => {
      card.style.display = (cat === 'all' || card.dataset.cat === cat) ? '' : 'none';
    });
  }

  /* Live search */
  function liveFilter(val) {
    const q = val.toLowerCase();
    document.querySelectorAll('.component-card').forEach(card => {
      const match = card.dataset.name.toLowerCase().includes(q) ||
        card.querySelector('.card-label')?.textContent.toLowerCase().includes(q);
      card.style.display = match ? '' : 'none';
    });
  }

  /* Scroll animations */
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in-view'); });
  }, { threshold: 0.08 });
  document.querySelectorAll('.component-card').forEach(el => observer.observe(el));
</script>
</body>
</html>
'''
    lines = lines[:idx] + [correct]
    with open('e:/nsoc26/UI-Verse/navbar.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Fixed footer!')
else:
    print('Footer not found!')
