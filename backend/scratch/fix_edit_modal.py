import re

with open('users/templates/users/profile.html', 'r') as f:
    content = f.read()

# Fix the edit modal
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

# Replace the old fields block inside the Edit Details Modal
pattern = r'{%\s*if \'Individual Applicant\' in request.user.all_roles\s*%}.*?{%\s*endif\s*%}'
content = re.sub(pattern, edit_modal_individual, content, flags=re.DOTALL)

with open('users/templates/users/profile.html', 'w') as f:
    f.write(content)
