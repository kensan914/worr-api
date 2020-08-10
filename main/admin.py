from django.contrib import admin
from .models import User, Connection, Voice


admin.site.register(User)
admin.site.register(Connection)
admin.site.register(Voice)
