import re

html_block = """                        <div class="row g-3 mb-4">
                            <div class="col-md-12">
                                <label class="form-label fw-bold">Ujuzi katika Tiba Asili / Miti Dawa</label><br>
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
                                <h6 class="fw-bold text-muted">Iwapo umepata mafunzo rasmi:</h6>
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label">{{ form.training_institution.label }}</label>
                                        {{ form.training_institution }}
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">{{ form.training_duration.label }}</label>
                                        {{ form.training_duration }}
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">{{ form.training_duration_type.label }}</label>
                                        {{ form.training_duration_type }}
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-12 mt-3" id="skills_kurithi_container" style="display: none;">
                                <h6 class="fw-bold text-muted">Iwapo umerithi ujuzi huo:</h6>
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label">{{ form.inherited_from.label }}</label>
                                        {{ form.inherited_from }}
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">{{ form.inherited_duration.label }}</label>
                                        {{ form.inherited_duration }}
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">{{ form.inherited_duration_type.label }}</label>
                                        {{ form.inherited_duration_type }}
                                    </div>
                                </div>
                            </div>

                            <div class="col-md-12 mt-3" id="traditional_medicine_skills_other_container" style="display: none;">
                                <h6 class="fw-bold text-muted">{{ form.traditional_medicine_skills_other.label }}:</h6>
                                {{ form.traditional_medicine_skills_other }}
                            </div>
                        </div>"""

def update_file(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Replacing the whole row g-3 mb-4 that contains the old numbering and old fields
    pattern_html = re.compile(r'<div class="row g-3 mb-4">\s*<div class="col-md-12">\s*<label class="form-label fw-bold">1\.7\..*?</label>.*?</div>\s*</div>', re.DOTALL)
    if pattern_html.search(content):
        content = pattern_html.sub(html_block, content)
    
    with open(filename, 'w') as f:
        f.write(content)

update_file('medicines/templates/medicines/apply_listing.html')
update_file('medicines/templates/medicines/apply_category_ii.html')
