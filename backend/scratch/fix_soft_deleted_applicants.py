from users.models import Applicant

# Find all softly deleted applicants and hard delete them
soft_deleted_applicants = Applicant.all_objects.filter(is_deleted=True)
count = soft_deleted_applicants.count()
print(f'Found {count} soft-deleted applicants. Hard deleting them...')

for applicant in soft_deleted_applicants:
    applicant.hard_delete()

print('Done.')
