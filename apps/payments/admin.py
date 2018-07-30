from django.contrib import admin
from django.shortcuts import get_object_or_404
from .models import AccessToken, TokenApplication, AccessCard, Plan
from config.utils import pin_generator
# Register your models here.
@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('token_application', 'token')

    def save_model(self, request, obj, form, change):
        if obj.token:
            pass
        else:
            obj.token = 'TOKEN-'+pin_generator(length=15)
            token_application = get_object_or_404(TokenApplication, application_id=obj.token_application.application_id)
            token_application.status = 'A'
            token_application.save()
        super(AccessTokenAdmin, self).save_model(request, obj, form, change)


@admin.register(TokenApplication)
class TokenApplicationAdmin(admin.ModelAdmin):
    list_display = ('school','term','year','application_id', 'status')


@admin.register(AccessCard)
class AccessCardAdmin(admin.ModelAdmin):
    list_display = ('student','access_code','term', 'year','school_token')

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_code', 'amount', 'student_limit', 'staff_limit')