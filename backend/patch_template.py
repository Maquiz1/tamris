import re

def update_template(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Update Title
    content = content.replace(
        "Apply for Category II Registration - TAMRIS",
        "Maombi ya Uorodheshwaji / Usajili wa Dawa Asili"
    )
    content = content.replace(
        '<h2 class="mb-0 fs-4">Maombi ya Usajili wa Dawa Aina ya 2</h2>',
        '<h2 class="mb-0 fs-4">Maombi ya Uorodheshwaji / Usajili wa Dawa Asili ({{ application.get_application_type_display }})</h2>'
    )
    # The current template says Maombi ya Usajili wa Dawa Aina ya 2. Let's make sure it handles both.
    
    # Add hidden input for application type
    hidden_input = '<input type="hidden" id="sys_application_type" value="{{ application.application_type }}">'
    content = content.replace('<form method="post" enctype="multipart/form-data" id="applicationForm">', '<form method="post" enctype="multipart/form-data" id="applicationForm">\n    ' + hidden_input)

    # Add dynamic JS logic at the end of the script block
    js_code = """
    // --- Unified Master Form Logic ---
    const appType = document.getElementById('sys_application_type').value;

    const cat2Fields = [
        'id_shelf_life', 'id_dosage', 'id_quality_control_procedures', 
        'id_in_process_control_procedures', 'id_manufacturing_flow_chart',
        'id_brela_registration_name', 'id_scientific_name_report', 
        'id_heavy_metals_report', 'id_pesticides_report', 'id_toxic_chemicals_report', 
        'id_conventional_drugs_report', 'id_foreign_matter_report', 'id_microbes_report', 
        'id_aflatoxin_report', 'id_toxicity_report', 'id_stability_report', 
        'id_moisture_analysis_report', 'id_ph_analysis_report', 
        'id_uniformity_test_report', 'id_dissolution_test_report', 
        'id_clinical_observation_report'
    ];
    
    const listingFields = [
        'id_other_appearance_instructions'
    ];

    function toggleFields(fields, show) {
        fields.forEach(function(fieldId) {
            const field = document.getElementById(fieldId);
            if (field) {
                const container = field.closest('.mb-4') || field.closest('.mb-3') || field.closest('.col-md-6') || field.closest('.col-md-12');
                if (container) {
                    if (show) {
                        container.style.display = 'block';
                    } else {
                        container.style.display = 'none';
                        field.removeAttribute('required');
                    }
                }
            }
        });
    }

    if (appType === 'LISTING') {
        toggleFields(cat2Fields, false);
        toggleFields(listingFields, true);
        
        // Hide Section 13 (Technical Attachments) header if it exists
        const section13Header = Array.from(document.querySelectorAll('h4')).find(el => el.textContent.includes('13.'));
        if(section13Header) section13Header.style.display = 'none';
    } else if (appType === 'CATEGORY_II') {
        toggleFields(cat2Fields, true);
        toggleFields(listingFields, false);
    }
    """
    
    # Insert JS before </script> at the end
    content = content.replace("</script>\n{% endblock %}", js_code + "\n</script>\n{% endblock %}")

    with open(filename, 'w') as f:
        f.write(content)

update_template('medicines/templates/medicines/apply_master.html')
