from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import (
    CustomUser, Role, StaffProfile,
    Applicant, Individual, Organization,
    ApplicantIdentity, ApplicantAddress, ApplicantContact,
    Education, OrganizationRepresentative, ApplicantDocument
)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'role')

class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'role')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    ordering = ('email',)
    list_display = ('email', 'role', 'is_staff', 'is_superuser', 'is_email_verified')
    search_fields = ('email', 'phone_number')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone_number', 'role', 'is_email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('user', 'applicant_type', 'application_no', 'status')
    search_fields = ('user__email', 'application_no')
    list_filter = ('applicant_type', 'status')

@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'applicant')
    search_fields = ('first_name', 'last_name', 'applicant__user__email')

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'registration_number', 'tin', 'applicant')
    search_fields = ('organization_name', 'tin', 'registration_number', 'applicant__user__email')

@admin.register(ApplicantIdentity)
class ApplicantIdentityAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'identity_type', 'identity_number', 'is_primary')

@admin.register(OrganizationRepresentative)
class OrganizationRepresentativeAdmin(admin.ModelAdmin):
    list_display = ('organization', 'first_name', 'last_name', 'position', 'is_primary')

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'designation', 'department')
    search_fields = ('user__email', 'employee_id', 'designation')
