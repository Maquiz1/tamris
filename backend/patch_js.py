import re

js_block_old = """
        const inputs = {
            'MAFUNZO': [document.getElementById('id_training_institution'), document.getElementById('id_training_duration')],
            'KURITHI': [document.getElementById('id_inherited_from'), document.getElementById('id_inherited_duration')],
            'MENGINEYO': [document.getElementById('id_traditional_medicine_skills_other')]
        };"""

js_block_new = """
        const inputs = {
            'MAFUNZO': [document.getElementById('id_training_institution'), document.getElementById('id_training_duration'), document.getElementById('id_training_duration_type')],
            'KURITHI': [document.getElementById('id_inherited_from'), document.getElementById('id_inherited_duration'), document.getElementById('id_inherited_duration_type')],
            'MENGINEYO': [document.getElementById('id_traditional_medicine_skills_other')]
        };"""

def update_file(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Replacing JS block
    content = content.replace(js_block_old, js_block_new)
    
    with open(filename, 'w') as f:
        f.write(content)

update_file('medicines/templates/medicines/apply_listing.html')
update_file('medicines/templates/medicines/apply_category_ii.html')
