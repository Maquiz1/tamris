import re

with open('onboarding.html', 'r') as f:
    content = f.read()

# Restore CSS classes
css_append = """
  /* ── Original Side Nav ── */
  .ob-sidenav { border-right:1px solid #e2e8f0; padding:1.25rem .75rem; background:#fafafa; min-height:100%; }
  .ob-sidenav-title { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#94a3b8; padding:0 .5rem .5rem; margin-bottom:.25rem; }
  .ob-sidenav .nav-link { display:flex; align-items:center; gap:.6rem; padding:.65rem .85rem; border-radius:.5rem; color:#64748b; font-weight:600; font-size:.875rem; border:none; background:transparent; width:100%; text-align:left; transition:all .18s; margin-bottom:.2rem; text-decoration:none; }
  .ob-sidenav .nav-link:hover { background:var(--teal-light); color:var(--teal-dark); }
  .ob-sidenav .nav-link.active { background:var(--teal-light); color:var(--teal-dark); border-left:3px solid var(--teal-main); }
  .ob-sidenav .nav-link i { font-size:1.05rem; }
  .ob-sidenav .nav-link:disabled { opacity:.5; cursor:not-allowed; }
  .nav-badge { margin-left:auto; font-size:.65rem; font-weight:700; padding:.15rem .45rem; border-radius:20px; }
  .nav-badge.done { background:#d1fae5; color:#059669; }
  .nav-badge.now { background:var(--teal-main); color:#fff; }
  .nav-badge.todo { background:#f1f5f9; color:#64748b; }
  .nav-badge.locked { background:#f1f5f9; color:#94a3b8; }
  /* ── Top Tab Bar ── */
  .ob-top-tabs { border-bottom:1px solid #e2e8f0; background:#fff; padding:0 1.5rem; display:flex; align-items:stretch; gap:0; overflow-x:auto; flex-shrink:0; }
  .ob-top-tab { display:flex; align-items:center; gap:.4rem; padding:.85rem 1rem; border:none; background:transparent; color:#64748b; font-weight:600; font-size:.825rem; border-bottom:2px solid transparent; margin-bottom:-1px; cursor:pointer; transition:all .2s; white-space:nowrap; text-decoration:none; }
  .ob-top-tab i { font-size:.95rem; }
  .ob-top-tab:hover { color:var(--teal-dark); background:var(--teal-light); }
  .ob-top-tab.active { color:var(--teal-dark); border-bottom-color:var(--teal-main); }
  .req-dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:#ef4444; margin-left:.25rem; vertical-align:middle; }
"""

if "/* ── Original Side Nav" not in content:
    content = content.replace("/* ── Sub Sidebar ── */", css_append + "\n  /* ── Sub Sidebar ── */")

# Remove top stepper html
stepper_regex = re.compile(r'\{\# Top Stepper \#\}.*?</div>\s*</div>', re.DOTALL)
content = stepper_regex.sub('', content)

# Change row structure to include side nav
new_structure_start = """
  {# Main Card #}
  <div class="ob-body-card">
    <div class="row g-0" style="min-height:620px;">
      
      {# ═══ SIDEBAR ═══ #}
      <div class="col-md-3">
        <div class="ob-sidenav">
          <div class="ob-sidenav-title">Registration Steps</div>
          
          <a href="{% url 'users:onboarding' %}?step=1" class="nav-link {% if step == 1 %}active{% endif %}">
            <i class="ri-user-settings-line"></i> Role
            {% if step > 1 %}<span class="nav-badge done"><i class="ri-check-line"></i></span>
            {% elif step == 1 %}<span class="nav-badge now">Now</span>
            {% endif %}
          </a>
          
          <a href="{% if unlocked_step >= 2 %}{% url 'users:onboarding' %}?step=2{% else %}#{% endif %}" class="nav-link {% if step == 2 %}active{% endif %}" {% if unlocked_step < 2 %}disabled{% endif %}>
            <i class="ri-team-line"></i> Demographics
            {% if step > 2 %}<span class="nav-badge done"><i class="ri-check-line"></i></span>
            {% elif step == 2 %}<span class="nav-badge now">Now</span>
            {% elif unlocked_step < 2 %}<span class="nav-badge locked"><i class="ri-lock-line"></i></span>
            {% else %}<span class="nav-badge todo">Todo</span>
            {% endif %}
          </a>
          
          <a href="{% if unlocked_step >= 3 %}{% url 'users:onboarding' %}?step=3{% else %}#{% endif %}" class="nav-link {% if step == 3 %}active{% endif %}" {% if unlocked_step < 3 %}disabled{% endif %}>
            <i class="ri-file-shield-2-line"></i> Attachments
            {% if step > 3 %}<span class="nav-badge done"><i class="ri-check-line"></i></span>
            {% elif step == 3 %}<span class="nav-badge now">Now</span>
            {% elif unlocked_step < 3 %}<span class="nav-badge locked"><i class="ri-lock-line"></i></span>
            {% else %}<span class="nav-badge todo">Todo</span>
            {% endif %}
          </a>
          
          <a href="{% if unlocked_step >= 4 %}{% url 'users:onboarding' %}?step=4{% else %}#{% endif %}" class="nav-link {% if step == 4 %}active{% endif %}" {% if unlocked_step < 4 %}disabled{% endif %}>
            <i class="ri-checkbox-circle-line"></i> Submit
            {% if step == 4 %}<span class="nav-badge now">Now</span>
            {% elif unlocked_step < 4 %}<span class="nav-badge locked"><i class="ri-lock-line"></i></span>
            {% else %}<span class="nav-badge todo">Todo</span>
            {% endif %}
          </a>

        </div>
      </div>

      {# ═══ CONTENT ═══ #}
      <div class="col-md-9 ob-right">
"""

content = re.sub(r'\{\# Main Card \#\}.*?\{\# ═══ CONTENT ═══ \#\}\s*<div class="col-12">', new_structure_start, content, flags=re.DOTALL)

# Refactor Step 1 (Role)
role_start = """
        {# ─── ROLE (Step 1) ─── #}
        <div id="section-role" class="section-wrapper {% if step != 1 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-apptype" onclick="switchTopTab('role','apptype')" type="button">
              <i class="ri-list-settings-line"></i> Applicant Type <span class="req-dot"></span>
            </button>
          </div>
"""
content = re.sub(r'\{\# ─── ROLE \(Step 1\) ─── \#\}.*?<div class="col-md-9 d-flex flex-column">', role_start, content, flags=re.DOTALL)

# Refactor Step 2 (Demographics)
demo_start = """
        {# ─── DEMOGRAPHICS (Step 2) ─── #}
        <div id="section-demographics" class="section-wrapper {% if step != 2 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-identity" onclick="switchTopTab('demographics','identity')" type="button">
              <i class="ri-team-line"></i> Identity <span class="req-dot"></span>
            </button>
            <button class="ob-top-tab" id="toptab-address" onclick="switchTopTab('demographics','address')" type="button">
              <i class="ri-map-pin-line"></i> Address <span class="req-dot"></span>
            </button>
            <button class="ob-top-tab" id="toptab-contacts" onclick="switchTopTab('demographics','contacts')" type="button">
              <i class="ri-phone-line"></i> Contacts <span class="req-dot"></span>
            </button>
          </div>
"""
content = re.sub(r'\{\# ─── DEMOGRAPHICS \(Step 2\) ─── \#\}.*?<div class="col-md-9 d-flex flex-column">', demo_start, content, flags=re.DOTALL)

# Refactor Step 3 (Attachments)
att_start = """
        {# ─── ATTACHMENTS (Step 3) ─── #}
        <div id="section-attachments" class="section-wrapper {% if step != 3 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-required" onclick="switchTopTab('attachments','required')" type="button">
              <i class="ri-file-shield-2-line"></i> Required Documents <span class="req-dot"></span>
            </button>
            <button class="ob-top-tab" id="toptab-optional" onclick="switchTopTab('attachments','optional')" type="button">
              <i class="ri-file-add-line"></i> Optional Documents
            </button>
          </div>
"""
content = re.sub(r'\{\# ─── ATTACHMENTS \(Step 3\) ─── \#\}.*?<div class="col-md-9 d-flex flex-column">', att_start, content, flags=re.DOTALL)

# Refactor Step 4 (Submit)
sub_start = """
        {# ─── SUBMIT (Step 4) ─── #}
        <div id="section-final" class="section-wrapper {% if step != 4 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-submit" onclick="switchTopTab('final','submit')" type="button">
              <i class="ri-checkbox-circle-line"></i> Submit <span class="req-dot"></span>
            </button>
          </div>
"""
content = re.sub(r'\{\# ─── FINAL / SUBMIT \(Step 4\) ─── \#\}.*?<div class="col-md-9 d-flex flex-column">', sub_start, content, flags=re.DOTALL)

# Remove stray closing div tags for the old sub-sidenav row structure
content = content.replace("            </div><!-- /col-9 -->\n          </div><!-- /row -->", "")

with open('onboarding.html', 'w') as f:
    f.write(content)

