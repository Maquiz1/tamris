from users.models import Applicant, ApplicantAddress

app = Applicant.objects.first()
if app:
    print(f"Applicant ID: {app.id}")
    addresses = ApplicantAddress.objects.filter(applicant=app)
    print(f"Addresses count: {addresses.count()}")
    for a in addresses:
        print(a.region, a.district, a.ward, a.street, a.physical_address)
else:
    print("No applicant found")
