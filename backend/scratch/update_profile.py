import re

with open('users/templates/users/profile.html', 'r') as f:
    content = f.read()

# Replace `request.user.user_profile.XXX` with `docs.XXX`
# and `request.user.company_profile.XXX` with `docs.XXX`
# BUT ONLY within the Uploaded Documents section (lines 206 onwards)

section_start = content.find('<!-- Uploaded Documents -->')
top_part = content[:section_start]
bottom_part = content[section_start:]

# Replace user_profile.doc and company_profile.doc with docs.doc
import re
bottom_part = re.sub(r'request\.user\.user_profile\.([a-zA-Z_]+)', r'docs.\1', bottom_part)
bottom_part = re.sub(r'request\.user\.company_profile\.([a-zA-Z_]+)', r'docs.\1', bottom_part)

# Replace url with file.url
bottom_part = re.sub(r'docs\.([a-zA-Z_]+)\.url', r'docs.\1.file.url', bottom_part)

# Now, we need to find the `<td>` that contains the Action buttons and replace the logic.
# The pattern we want to replace is:
# {% if docs.XXX %}
#     <button type="button" class="btn btn-sm btn-outline-primary view-doc-btn" data-url="{{ docs.XXX.file.url }}">
#         <i class="bi bi-eye"></i> View
#     </button>
# {% else %}
#     <span class="text-muted small"><i class="bi bi-cloud-upload me-1"></i>Not uploaded</span>
# {% endif %}
# {% if request.user.document_statuses.XXX.status == 'REJECTED' %}
#     <form method="post" action="{% url 'users:reupload_document' %}" enctype="multipart/form-data" class="m-0">
#         ...
#     </form>
# {% endif %}

# Let's write a regex that matches the entire <td> block for the actions and replaces it.

def replace_action_td(match):
    doc_key = match.group(1)
    # the ID of the file input might be different, let's extract it from the original
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

with open('users/templates/users/profile.html', 'w') as f:
    f.write(top_part + bottom_part)
