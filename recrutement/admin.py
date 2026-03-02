from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

# Enregistrement des modèles dans l'admin
admin.site.register(Administration)
admin.site.register(Adresse)
admin.site.register(Offre)
admin.site.register(CandidatProfile)
admin.site.register(Candidature)
admin.site.register(AdministrateurRH)
admin.site.register(SuperAdmin)
admin.site.register(CandidatFavoris)

# Extension du User admin pour ajouter des infos
class CandidatProfileInline(admin.StackedInline):
    model = CandidatProfile
    can_delete = False
    verbose_name_plural = 'Profil Candidat'

class AdministrateurRHInline(admin.StackedInline):
    model = AdministrateurRH
    can_delete = False
    verbose_name_plural = 'Profil Administrateur RH'

class SuperAdminInline(admin.StackedInline):
    model = SuperAdmin
    can_delete = False
    verbose_name_plural = 'Profil Super Admin'

# Personnaliser l'admin User
class CustomUserAdmin(UserAdmin):
    inlines = (CandidatProfileInline, AdministrateurRHInline, SuperAdminInline)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Désenregistrer et réenregistrer User avec notre admin personnalisé
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

from .models import Notification

admin.site.register(Notification)

class NotificationAdmin(admin.ModelAdmin):
    # Si vous avez défini ceci, il peut filtrer les résultats
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(...)  # ← Vérifiez ici