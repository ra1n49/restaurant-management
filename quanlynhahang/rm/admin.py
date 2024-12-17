from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

# Register your models here.
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'chucvu', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('chucvu', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'chucvu')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Ban)
admin.site.register(Menu)
admin.site.register(Order)
admin.site.register(ChiTietOrder)
admin.site.register(LichLamViec)





