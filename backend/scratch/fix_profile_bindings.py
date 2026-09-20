import re

with open('users/templates/users/profile.html', 'r') as f:
    content = f.read()

# Replace individual fields
replacements = {
    r'request\.user\.user_profile\.full_name': r'request.user.applicant_profile.individual.full_name',
    r'request\.user\.user_profile\.sex': r'request.user.applicant_profile.individual.sex',
    r'request\.user\.user_profile\.age': r'request.user.applicant_profile.individual.date_of_birth',
    r'request\.user\.user_profile\.formatted_nida': r'request.user.applicant_profile.identity_obj.formatted_id_number',
    r'request\.user\.user_profile\.formatted_tin': r'request.user.applicant_profile.individual.tin',
    r'request\.user\.user_profile\.education_level': r'request.user.applicant_profile.education_obj.education_level',
    r'request\.user\.user_profile\.residency_duration': r'request.user.applicant_profile.address_obj.residency_duration',
    r'request\.user\.user_profile\.country': r'request.user.applicant_profile.address_obj.country',
    r'request\.user\.user_profile\.region': r'request.user.applicant_profile.address_obj.region',
    r'request\.user\.user_profile\.district': r'request.user.applicant_profile.address_obj.district',
    r'request\.user\.user_profile\.ward': r'request.user.applicant_profile.address_obj.ward',
    r'request\.user\.user_profile\.village_street': r'request.user.applicant_profile.address_obj.street',
    r'request\.user\.user_profile\.postal_address': r'request.user.applicant_profile.address_obj.postal_address',
    r'request\.user\.user_profile\.landline_phone': r'request.user.applicant_profile.contact_obj.landline',
    r'request\.user\.user_profile\.address': r'request.user.applicant_profile.address_obj.physical_address',

    r'request\.user\.company_profile\.company_name': r'request.user.applicant_profile.organization.organization_name',
    r'request\.user\.company_profile\.brela_number': r'request.user.applicant_profile.organization.registration_number',
    r'request\.user\.company_profile\.formatted_tin': r'request.user.applicant_profile.organization.tin',
    r'request\.user\.company_profile\.country': r'request.user.applicant_profile.address_obj.country',
    r'request\.user\.company_profile\.region': r'request.user.applicant_profile.address_obj.region',
    r'request\.user\.company_profile\.district': r'request.user.applicant_profile.address_obj.district',
    r'request\.user\.company_profile\.ward': r'request.user.applicant_profile.address_obj.ward',
    r'request\.user\.company_profile\.village_street': r'request.user.applicant_profile.address_obj.street',
    r'request\.user\.company_profile\.postal_address': r'request.user.applicant_profile.address_obj.postal_address',
    r'request\.user\.company_profile\.fax': r'request.user.applicant_profile.contact_obj.fax',
    r'request\.user\.company_profile\.physical_address': r'request.user.applicant_profile.address_obj.physical_address',
}

for old, new in replacements.items():
    content = re.sub(old, new, content)

with open('users/templates/users/profile.html', 'w') as f:
    f.write(content)
