import re

with open('scratch/profile_original.html', 'r') as f:
    content = f.read()

# 1. Fix the top section display fields for Individual
content = content.replace('request.user.user_profile.full_name', 'request.user.applicant_profile.individual.full_name')
content = content.replace('request.user.user_profile.sex', 'request.user.applicant_profile.individual.sex')
content = content.replace('request.user.user_profile.age', 'request.user.applicant_profile.individual.date_of_birth')
content = content.replace('request.user.user_profile.formatted_nida', 'request.user.applicant_profile.identity_obj.formatted_id_number')
content = content.replace('request.user.user_profile.formatted_tin', 'request.user.applicant_profile.individual.tin')
content = content.replace('request.user.user_profile.education_level', 'request.user.applicant_profile.education_obj.education_level')
content = content.replace('request.user.user_profile.residency_duration', 'request.user.applicant_profile.address_obj.residency_duration')
content = content.replace('request.user.user_profile.country', 'request.user.applicant_profile.address_obj.country')
content = content.replace('request.user.user_profile.region', 'request.user.applicant_profile.address_obj.region')
content = content.replace('request.user.user_profile.district', 'request.user.applicant_profile.address_obj.district')
content = content.replace('request.user.user_profile.ward', 'request.user.applicant_profile.address_obj.ward')
content = content.replace('request.user.user_profile.village_street', 'request.user.applicant_profile.address_obj.street')
content = content.replace('request.user.user_profile.postal_address', 'request.user.applicant_profile.address_obj.postal_address')
content = content.replace('request.user.user_profile.landline_phone', 'request.user.applicant_profile.contact_obj.landline')
content = content.replace('request.user.user_profile.address', 'request.user.applicant_profile.address_obj.physical_address')

# 2. Fix the top section display fields for Company
content = content.replace('request.user.company_profile.company_name', 'request.user.applicant_profile.organization.organization_name')
content = content.replace('request.user.company_profile.brela_number', 'request.user.applicant_profile.organization.registration_number')
content = content.replace('request.user.company_profile.formatted_tin', 'request.user.applicant_profile.organization.tin')
content = content.replace('request.user.company_profile.country', 'request.user.applicant_profile.address_obj.country')
content = content.replace('request.user.company_profile.region', 'request.user.applicant_profile.address_obj.region')
content = content.replace('request.user.company_profile.district', 'request.user.applicant_profile.address_obj.district')
content = content.replace('request.user.company_profile.ward', 'request.user.applicant_profile.address_obj.ward')
content = content.replace('request.user.company_profile.village_street', 'request.user.applicant_profile.address_obj.street')
content = content.replace('request.user.company_profile.postal_address', 'request.user.applicant_profile.address_obj.postal_address')
content = content.replace('request.user.company_profile.fax', 'request.user.applicant_profile.contact_obj.fax')
content = content.replace('request.user.company_profile.physical_address', 'request.user.applicant_profile.address_obj.physical_address')

# 3. Fix Uploaded Documents Section
# In this section, we replace request.user.user_profile.XXX with docs.XXX
# We must ONLY do this for the "Uploaded Documents" section to avoid breaking anything else.
section_start = content.find('<!-- Uploaded Documents -->')
top_part = content[:section_start]
bottom_part = content[section_start:]

bottom_part = re.sub(r'request\.user\.user_profile\.([a-zA-Z_]+)', r'docs.\1', bottom_part)
bottom_part = re.sub(r'request\.user\.company_profile\.([a-zA-Z_]+)', r'docs.\1', bottom_part)
bottom_part = re.sub(r'docs\.([a-zA-Z_]+)\.url', r'docs.\1.file.url', bottom_part)

def replace_action_td(match):
    doc_key = match.group(1)
    form_html = match.group(2)
    input_id = re.search(r'id="(reupload_[a-zA-Z_]+)"', form_html).group(1)
    
    new_td = f"""<div class="d-flex align-items-center gap-2">
                                            {{% if docs.{doc_key} %}}
                                                <button type="button" class="btn btn-sm btn-outline-primary view-doc-btn" data-url="{{{{ docs.{doc_key}.file.url }}}}">
                                                    <i class="bi bi-eye"></i> View
                                                </button>
                                            {{% endif %}}
                                            {{% if request.user.document_statuses.{doc_key}.status == 'REJECTED' or not docs.{doc_key} %}}
                                                <form method="post" action="{{% url 'users:reupload_document' %}}" enctype="multipart/form-data" class="m-0">
                                                    {{% csrf_token %}}
                                                    <input type="hidden" name="doc_key" value="{doc_key}">
                                                    <input type="file" name="document" class="d-none" id="{input_id}" onchange="this.form.submit()" accept=".pdf,.jpg,.jpeg,.png" required>
                                                    <label for="{input_id}" class="btn btn-sm {{% if docs.{doc_key} %}}btn-danger{{% else %}}btn-primary{{% endif %}} mb-0" style="cursor: pointer;">
                                                        <i class="bi bi-upload"></i> {{% if docs.{doc_key} %}}Re-upload{{% else %}}Upload{{% endif %}}
                                                    </label>
                                                </form>
                                            {{% endif %}}
                                        </div>"""
    return new_td

pattern = r'<div class="d-flex align-items-center gap-2">\s*{% if docs\.([a-zA-Z_]+) %}.*?{% else %}\s*<span class="text-muted small">.*?</span>\s*{% endif %}\s*{% if request\.user\.document_statuses\.\1\.status == \'REJECTED\' %}\s*(<form method="post" action="{% url \'users:reupload_document\' %}".*?</form>)\s*{% endif %}\s*</div>'

bottom_part = re.sub(pattern, replace_action_td, bottom_part, flags=re.DOTALL)

# Reconstruct content
content = top_part + bottom_part

# 4. Update the Edit Details Modal
edit_modal_individual = """
          {% if 'Individual Applicant' in request.user.all_roles %}
            <div class="mb-3">
              <label class="form-label fw-bold">First Name <span class="text-danger">*</span></label>
              <input type="text" name="first_name" class="form-control" value="{{ request.user.applicant_profile.individual.first_name }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Middle Name</label>
              <input type="text" name="middle_name" class="form-control" value="{{ request.user.applicant_profile.individual.middle_name|default:'' }}">
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Last Name <span class="text-danger">*</span></label>
              <input type="text" name="last_name" class="form-control" value="{{ request.user.applicant_profile.individual.last_name }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">ID Number <span class="text-danger">*</span></label>
              <input type="text" name="identity_number" class="form-control" value="{{ request.user.applicant_profile.identity_obj.identity_number }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">TIN Number <span class="text-danger">*</span></label>
              <input type="text" name="tin" class="form-control" value="{{ request.user.applicant_profile.individual.tin }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Physical Address <span class="text-danger">*</span></label>
              <textarea name="physical_address" class="form-control" rows="3" required>{{ request.user.applicant_profile.address_obj.physical_address }}</textarea>
            </div>
          {% elif 'Company Applicant' in request.user.all_roles %}
            <div class="mb-3">
              <label class="form-label fw-bold">Company Name <span class="text-danger">*</span></label>
              <input type="text" name="company_name" class="form-control" value="{{ request.user.applicant_profile.organization.organization_name }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Registration Number <span class="text-danger">*</span></label>
              <input type="text" name="registration_number" class="form-control" value="{{ request.user.applicant_profile.organization.registration_number }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">TIN Number <span class="text-danger">*</span></label>
              <input type="text" name="tin" class="form-control" value="{{ request.user.applicant_profile.organization.tin }}" required>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Physical Address <span class="text-danger">*</span></label>
              <textarea name="physical_address" class="form-control" rows="3" required>{{ request.user.applicant_profile.address_obj.physical_address }}</textarea>
            </div>
          {% endif %}
"""

# The Edit modal is currently:
#           {% if 'Individual Applicant' in request.user.all_roles %}
#             <div class="mb-3">
#               <label class="form-label fw-bold">Full Name <span class="text-danger">*</span></label>
# ...
#           {% endif %}
# Let's replace the whole block in Edit Details Modal using a tight regex.
# We know it starts right after <input type="hidden" name="action" value="edit_details"> and <div class="modal-body">
# and the phone number input block.
# Let's just find `{% if 'Individual Applicant' in request.user.all_roles %}` and `{% endif %}` within the modal.
modal_idx = content.find('<!-- Edit Details Modal -->')
if modal_idx != -1:
    modal_content = content[modal_idx:]
    pre_modal_content = content[:modal_idx]
    edit_modal_pattern = r'{%\s*if \'Individual Applicant\' in request.user.all_roles\s*%}.*?{%\s*endif\s*%}'
    modal_content = re.sub(edit_modal_pattern, edit_modal_individual.strip(), modal_content, flags=re.DOTALL)
    content = pre_modal_content + modal_content


with open('users/templates/users/profile.html', 'w') as f:
    f.write(content)
