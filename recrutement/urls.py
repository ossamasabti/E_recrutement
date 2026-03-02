from django.urls import path
from django.contrib import admin
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ========== PAGES PUBLIQUES ==========
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('administrations/', views.liste_administrations, name='liste_administrations'),
    path('rh/dashboard/', views.rh_dashboard, name='rh_dashboard'),
    path('api/administration/<int:admin_id>/', views.administration_detail_json, name='administration_detail_json'),
    path('api/administration/<int:admin_id>/offres/', views.administration_offres_json, name='administration_offres_json'),
    
    # ========== OFFRE PUBLIQUE ==========
    path('offres/', views.liste_offres, name='liste_offres'),
    path('offre/<int:offre_id>/', views.detail_offre, name='detail_offre'),
    path('offre/<int:offre_id>/postuler/', views.postuler, name='postuler'),
    
    # ========== GESTION DES CANDIDATURES ==========
    path('candidatures/', views.gestion_candidatures, name='gestion_candidatures'),
    path('candidatures/<int:candidature_id>/changer-statut/', 
         views.changer_statut_candidature, name='changer_statut_candidature'),
    path('candidatures/<int:candidature_id>/commentaire/', 
         views.ajouter_commentaire_rh, name='ajouter_commentaire_rh'),
    path('candidatures/<int:candidature_id>/supprimer/', 
         views.supprimer_candidature, name='supprimer_candidature'),
    path('candidatures/export/', views.export_candidatures, name='export_candidatures'),
    
    # ========== PROFIL UTILISATEUR ==========
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # ========== CANDIDATURES UTILISATEUR ==========
    path('mes-candidatures/', views.mes_candidatures, name='mes_candidatures'),
    path('annuler-candidature/<int:candidature_id>/', views.annuler_candidature, name='annuler_candidature'),
    
    # ========== DASHBOARDS ==========
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # ========== GESTION DES OFFRES ==========
    path('gestion/offres/', views.admin_liste_offres, name='admin_liste_offres'),
    path('gestion-offres/', views.gestion_offres, name='gestion_offres'),
    
    # ========== NOTIFICATIONS ==========
    # CORRECTION : Gardez seulement UNE fois ces URLs
    path('notifications/', views.notifications_view, name='notifications_view'),  # J'utilise 'notifications_view' pour être cohérent
    path('notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('notifications/badge/', views.notification_badge, name='notification_badge'),
    
    # ========== API ENDPOINTS ==========
    path('api/offres/', views.get_offres_json, name='get_offres_json'),
    path('api/offres/<int:offre_id>/', views.get_offre_detail_json, name='get_offre_detail_json'),
    path('api/offres/create/', views.create_offre_api, name='create_offre_api'),
    path('api/offres/<int:offre_id>/update/', views.update_offre_api, name='update_offre_api'),
    path('api/offres/<int:offre_id>/delete/', views.delete_offre_api, name='delete_offre_api'),
    path('api/offres/bulk-action/', views.bulk_action_api, name='bulk_action_api'),
    
    # ========== GESTION DES UTILISATEURS ==========
    path('gestion-utilisateurs/', views.gestion_utilisateurs, name='gestion_utilisateurs'),
    path('gestion-utilisateurs/<int:user_id>/', views.detail_utilisateur, name='detail_utilisateur'),
    path('gestion-utilisateurs/<int:user_id>/modifier/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('gestion-utilisateurs/<int:user_id>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('gestion-utilisateurs/<int:user_id>/changer-statut/', views.changer_statut_utilisateur, name='changer_statut_utilisateur'),
    path('gestion-utilisateurs/creer/', views.creer_utilisateur_manuel, name='creer_utilisateur_manuel'),
    path('utilisateurs/<int:user_id>/update-permissions/', views.update_user_permissions, name='update_user_permissions'),
    
    # ========== MOT DE PASSE ==========
    path('forgot-password/', views.forgot_password_check, name='forgot_password_check'),
    path('reset-password/', views.reset_password_new_simple, name='reset_password_new'),
    
    # ========== ROUTES DE TEST ==========
    path('nouvelle-offre/', views.nouvelle_offre, name='nouvelle_offre'),
    path('form-test/', views.form_test, name='form_test'),


    path('gestion/administrations/', views.gestion_administrations, name='gestion_administrations'),
    path('gestion/administrations/creer/', views.creer_administration, name='creer_administration'),
    path('gestion/administrations/modifier/<int:id>/', views.modifier_administration, name='modifier_administration'),
    path('gestion/administrations/supprimer/<int:id>/', views.supprimer_administration, name='supprimer_administration'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)