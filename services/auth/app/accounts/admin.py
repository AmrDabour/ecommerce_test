from django.contrib import admin
from .models import User, CustomerProfile, VendorProfile

admin.site.register(User)
admin.site.register(CustomerProfile)
admin.site.register(VendorProfile)
