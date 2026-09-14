import re

with open('backend/users/templates/users/onboarding.html', 'r') as f:
    content = f.read()

# 1. Update CSS
css_add = """
  /* ── Top Stepper ── */
  .top-stepper-wrap { position:relative; margin-bottom: 2rem; padding: 0 1rem; }
  .stepper-line { position:absolute; top:15px; left:5%; right:5%; height:2px; background:#e2e8f0; z-index:1; }
  .stepper-progress { position:absolute; top:0; left:0; height:100%; background:var(--teal-main); transition:width 0.3s; }
  .stepper-container { position:relative; z-index:2; display:flex; justify-content:space-between; }
  .step-item { display:flex; flex-direction:column; align-items:center; gap:0.5rem; background:#f1f5f9; padding:0 10px; cursor:pointer; }
  .step-circle { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:600; font-size:0.9rem; border:2px solid #cbd5e1; background:#fff; color:#64748b; transition:all 0.2s; }
  .step-item.active .step-circle { border-color:var(--teal-main); background:var(--teal-main); color:#fff; }
  .step-item.done .step-circle { border-color:var(--teal-main); background:var(--teal-main); color:#fff; }
  .step-label { font-size:0.8rem; font-weight:700; color:#64748b; }
  .step-item.active .step-label, .step-item.done .step-label { color:var(--teal-main); }
  
  /* ── Sub Sidebar ── */
  .sub-sidenav { border-right:1px solid #e2e8f0; padding:1.25rem 0.75rem; background:#fff; min-height:100%; }
  .sub-sidenav .nav-link { display:flex; align-items:center; gap:0.6rem; padding:0.65rem 0.85rem; border-radius:0.5rem; color:#64748b; font-weight:600; font-size:0.875rem; border:none; background:transparent; width:100%; text-align:left; transition:all 0.18s; margin-bottom:0.2rem; }
  .sub-sidenav .nav-link:hover { background:var(--teal-light); color:var(--teal-dark); }
  .sub-sidenav .nav-link.active { background:var(--teal-light); color:var(--teal-dark); border-left:3px solid var(--teal-main); border-radius: 0 0.5rem 0.5rem 0; }
  .sub-sidenav .nav-link i { font-size:1.05rem; }
"""
content = content.replace("/* ── Side Nav ── */", css_add + "\n  /* ── Original Side Nav (Now unused, but keeping some styles) ── */")

# 2. Extract and remove the old left side menu
side_nav_pattern = re.compile(r'\{\# ═══ LEFT SIDE MENU ═══ \#\}.*?(?=\{\# ═══ RIGHT CONTENT ═══ \#\})', re.DOTALL)
content = side_nav_pattern.sub('', content)

# Remove the right content wrapper opening and closing div
content = content.replace('{# ═══ RIGHT CONTENT ═══ #}\n      <div class="col-md-10 ob-right">', '{# ═══ CONTENT ═══ #}\n      <div class="col-12">')
content = content.replace('</div>{# /col right #}', '</div>{# /col 12 #}')

# 3. Add Top Stepper before the Main Card
top_stepper = """
  {# Top Stepper #}
  <div class="top-stepper-wrap">
    <div class="stepper-line">
      <div class="stepper-progress" style="width: {% if step == 1 %}0%{% elif step == 2 %}33%{% elif step == 3 %}66%{% else %}100%{% endif %};"></div>
    </div>
    <div class="stepper-container">
      <div class="step-item {% if step >= 1 %}done{% endif %} {% if step == 1 %}active{% endif %}" onclick="switchSection('role')">
        <div class="step-circle">{% if step > 1 %}<i class="ri-check-line"></i>{% else %}1{% endif %}</div>
        <div class="step-label">Role</div>
      </div>
      <div class="step-item {% if step >= 2 %}done{% endif %} {% if step == 2 %}active{% endif %}" {% if unlocked_step >= 2 %}onclick="switchSection('demographics')"{% endif %}>
        <div class="step-circle">{% if step > 2 %}<i class="ri-check-line"></i>{% else %}2{% endif %}</div>
        <div class="step-label">Demographic</div>
      </div>
      <div class="step-item {% if step >= 3 %}done{% endif %} {% if step == 3 %}active{% endif %}" {% if unlocked_step >= 3 %}onclick="switchSection('attachments')"{% endif %}>
        <div class="step-circle">{% if step > 3 %}<i class="ri-check-line"></i>{% else %}3{% endif %}</div>
        <div class="step-label">Documents</div>
      </div>
      <div class="step-item {% if step >= 4 %}done{% endif %} {% if step == 4 %}active{% endif %}" {% if unlocked_step >= 4 %}onclick="switchSection('final')"{% endif %}>
        <div class="step-circle">{% if step > 4 %}<i class="ri-check-line"></i>{% else %}4{% endif %}</div>
        <div class="step-label">Submit</div>
      </div>
    </div>
  </div>
"""
content = content.replace('{# Main Card #}', top_stepper + '\n  {# Main Card #}')

# 4. Restructure each section
# Section Role
role_subnav = """
          <div class="row g-0 flex-grow-1">
            <div class="col-md-3 sub-sidenav">
              <button class="nav-link active" id="toptab-apptype" onclick="switchTopTab('role','apptype')" type="button">
                <i class="ri-list-settings-line"></i> Application Type
              </button>
            </div>
            <div class="col-md-9 d-flex flex-column">
"""
content = content.replace("""        <div id="section-role" class="section-wrapper {% if step != 1 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-apptype"
                    onclick="switchTopTab('role','apptype')" type="button">
              <i class="ri-list-settings-line"></i> Applicant Type
            </button>
          </div>""", f"""        <div id="section-role" class="section-wrapper {{% if step != 1 %}}d-none{{% endif %}}">
{role_subnav}""")
# Close the row for role
content = content.replace("""            </form>
          </div>
        </div>""", """            </form>
          </div>
            </div><!-- /col-9 -->
          </div><!-- /row -->
        </div>""")

# Section Demographics
demo_subnav = """
          <div class="row g-0 flex-grow-1">
            <div class="col-md-3 sub-sidenav">
              <button class="nav-link active" id="toptab-identity" onclick="switchTopTab('demographics','identity')" type="button">
                <i class="ri-team-line"></i> Demographic
              </button>
              <button class="nav-link" id="toptab-address" onclick="switchTopTab('demographics','address')" type="button">
                <i class="ri-map-pin-line"></i> Address
              </button>
              <button class="nav-link" id="toptab-contacts" onclick="switchTopTab('demographics','contacts')" type="button">
                <i class="ri-phone-line"></i> Contacts
              </button>
            </div>
            <div class="col-md-9 d-flex flex-column">
"""
content = content.replace("""        <div id="section-demographics" class="section-wrapper {% if step != 2 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-identity"
                    onclick="switchTopTab('demographics','identity')" type="button">
              <i class="ri-team-line"></i> Identity <span class="req-dot"></span>
            </button>
            <button class="ob-top-tab" id="toptab-address"
                    onclick="switchTopTab('demographics','address')" type="button">
              <i class="ri-map-pin-line"></i> Address <span class="req-dot"></span>
            </button>
            <button class="ob-top-tab" id="toptab-contacts"
                    onclick="switchTopTab('demographics','contacts')" type="button">
              <i class="ri-phone-line"></i> Contacts <span class="req-dot"></span>
            </button>
          </div>""", f"""        <div id="section-demographics" class="section-wrapper {{% if step != 2 %}}d-none{{% endif %}}">
{demo_subnav}""")
# Close row for demo
content = content.replace("""            </div>
          </form>
        </div>""", """            </div>
          </form>
            </div><!-- /col-9 -->
          </div><!-- /row -->
        </div>""")

# Section Attachments
attach_subnav = """
          <div class="row g-0 flex-grow-1">
            <div class="col-md-3 sub-sidenav">
              <button class="nav-link active" id="toptab-required" onclick="switchTopTab('attachments','required')" type="button">
                <i class="ri-file-shield-2-line"></i> Required Documents
              </button>
              <button class="nav-link" id="toptab-optional" onclick="switchTopTab('attachments','optional')" type="button">
                <i class="ri-file-add-line"></i> Optional Documents
              </button>
            </div>
            <div class="col-md-9 d-flex flex-column">
"""
content = content.replace("""        <div id="section-attachments" class="section-wrapper {% if step != 3 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-required"
                    onclick="switchTopTab('attachments','required')" type="button">
              <i class="ri-file-shield-2-line"></i> Required Documents <span class="req-dot"></span>
            </button>
            <button class="ob-top-tab" id="toptab-optional"
                    onclick="switchTopTab('attachments','optional')" type="button">
              <i class="ri-file-add-line"></i> Optional Documents
            </button>
          </div>""", f"""        <div id="section-attachments" class="section-wrapper {{% if step != 3 %}}d-none{{% endif %}}">
{attach_subnav}""")
# Close row for attach
content = content.replace("""            </div>
          </form>
        </div>""", """            </div>
          </form>
            </div><!-- /col-9 -->
          </div><!-- /row -->
        </div>""", 1)

# Section Final
final_subnav = """
          <div class="row g-0 flex-grow-1">
            <div class="col-md-3 sub-sidenav">
              <button class="nav-link active" id="toptab-submit" onclick="switchTopTab('final','submit')" type="button">
                <i class="ri-send-plane-line"></i> Submit
              </button>
            </div>
            <div class="col-md-9 d-flex flex-column">
"""
content = content.replace("""        <div id="section-final" class="section-wrapper {% if step != 4 %}d-none{% endif %}">
          <div class="ob-top-tabs">
            <button class="ob-top-tab active" id="toptab-submit"
                    onclick="switchTopTab('final','submit')" type="button">
              <i class="ri-send-plane-line"></i> Submit
            </button>
          </div>""", f"""        <div id="section-final" class="section-wrapper {{% if step != 4 %}}d-none{{% endif %}}">
{final_subnav}""")
# Close row for final
content = content.replace("""            </form>
          </div>
        </div>""", """            </form>
          </div>
            </div><!-- /col-9 -->
          </div><!-- /row -->
        </div>""", 1)

# Update Javascript switchTopTab to use .sub-sidenav instead of .ob-top-tabs
content = content.replace(
    "sectionEl.querySelectorAll('.ob-top-tab').forEach(function(t) { t.classList.remove('active'); });",
    "sectionEl.querySelectorAll('.nav-link').forEach(function(t) { t.classList.remove('active'); });"
)

with open('backend/users/templates/users/onboarding.html', 'w') as f:
    f.write(content)

print("done")
