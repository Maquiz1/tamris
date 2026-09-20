import re
import os

html_block = """                        <div class="row g-3 mb-4">
                            <div class="col-md-12">
                                <label class="form-label fw-bold">1.7. Ujuzi katika Tiba Asili / Miti Dawa</label><br>
                                <label class="form-label mb-2">{{ form.traditional_medicine_skills.label }} <span class="text-danger">*</span></label>
                                <div>
                                    {% for radio in form.traditional_medicine_skills %}
                                    <div class="form-check form-check-inline">
                                        {{ radio.tag }}
                                        <label class="form-check-label" for="{{ radio.id_for_label }}">{{ radio.choice_label }}</label>
                                    </div>
                                    {% endfor %}
                                </div>
                            </div>
                            
                            <div class="col-md-12 mt-3" id="skills_mafunzo_container" style="display: none;">
                                <h6 class="fw-bold text-muted">1.7.1. Iwapo umepata mafunzo rasmi:</h6>
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label">{{ form.training_institution.label }}</label>
                                        {{ form.training_institution }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">{{ form.training_duration.label }}</label>
                                        {{ form.training_duration }}
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-12 mt-3" id="skills_kurithi_container" style="display: none;">
                                <h6 class="fw-bold text-muted">1.7.2. Iwapo umerithi ujuzi huo:</h6>
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label">{{ form.inherited_from.label }}</label>
                                        {{ form.inherited_from }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">{{ form.inherited_duration.label }}</label>
                                        {{ form.inherited_duration }}
                                    </div>
                                </div>
                            </div>

                            <div class="col-md-12 mt-3" id="traditional_medicine_skills_other_container" style="display: none;">
                                <h6 class="fw-bold text-muted">1.7.3. {{ form.traditional_medicine_skills_other.label }}:</h6>
                                {{ form.traditional_medicine_skills_other }}
                            </div>
                        </div>"""

js_block = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const radios = document.querySelectorAll('input[name="traditional_medicine_skills"]');
        
        const containers = {
            'MAFUNZO': document.getElementById('skills_mafunzo_container'),
            'KURITHI': document.getElementById('skills_kurithi_container'),
            'MENGINEYO': document.getElementById('traditional_medicine_skills_other_container')
        };
        
        const inputs = {
            'MAFUNZO': [document.getElementById('id_training_institution'), document.getElementById('id_training_duration')],
            'KURITHI': [document.getElementById('id_inherited_from'), document.getElementById('id_inherited_duration')],
            'MENGINEYO': [document.getElementById('id_traditional_medicine_skills_other')]
        };
        
        function toggleSkills() {
            let selectedValue = null;
            radios.forEach(r => { if (r.checked) selectedValue = r.value; });
            
            Object.keys(containers).forEach(key => {
                if (containers[key]) {
                    if (key === selectedValue) {
                        containers[key].style.display = 'block';
                        inputs[key].forEach(i => { if (i) i.required = true; });
                    } else {
                        containers[key].style.display = 'none';
                        inputs[key].forEach(i => {
                            if (i) {
                                i.required = false;
                                i.value = '';
                            }
                        });
                    }
                }
            });
        }
        
        radios.forEach(r => r.addEventListener('change', toggleSkills));
        toggleSkills();
    });
</script>
"""

def update_file(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Replace HTML block
    # Finding the old row g-3 mb-4 that contains traditional_medicine_skills
    pattern_html = re.compile(r'<div class="row g-3 mb-4">\s*<div class="col-md-6">\s*<label class="form-label fw-bold">\{\{\s*form\.traditional_medicine_skills\.label.*?</label>.*?</div>\s*</div>', re.DOTALL)
    if pattern_html.search(content):
        content = pattern_html.sub(html_block, content)
    
    # Replace JS block
    pattern_js = re.compile(r'<script>\s*document\.addEventListener\("DOMContentLoaded", function\(\) \{\s*const skillSelect = document\.getElementById\("id_traditional_medicine_skills"\);.*?</script>', re.DOTALL)
    if pattern_js.search(content):
        content = pattern_js.sub(js_block, content)
    else:
        # Append to end of file if not found
        content += js_block
        
    with open(filename, 'w') as f:
        f.write(content)

update_file('medicines/templates/medicines/apply_listing.html')
update_file('medicines/templates/medicines/apply_category_ii.html')
