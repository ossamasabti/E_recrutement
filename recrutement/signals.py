from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Offre, Candidature, Notification
from django.db.models import Q

@receiver(post_save, sender=Offre)
def notify_new_offre(sender, instance, created, **kwargs):
    """Notifier les utilisateurs lorsqu'une nouvelle offre est créée"""
    if created and instance.statut == 'publiee':
        # Créer une notification pour tous les utilisateurs (sauf le créateur)
        users = User.objects.exclude(id=instance.createur.id)
        
        for user in users:
            Notification.objects.create(
                user=user,
                type_notification='offre',
                titre='Nouvelle offre disponible !',
                message=f"Une nouvelle offre '{instance.titre}' a été publiée par {instance.administration.nom}.",
                url=f"/offres/{instance.id_offre}/",
                related_offre=instance
            )

@receiver(post_save, sender=Candidature)
def notify_candidature_submitted(sender, instance, created, **kwargs):
    """Notifier le RH lorsqu'une candidature est soumise"""
    if created:
        # Notifier le RH qui a créé l'offre
        rh_user = instance.offre.createur
        
        Notification.objects.create(
            user=rh_user,
            type_notification='candidature',
            titre='Nouvelle candidature',
            message=f"{instance.candidat.get_full_name()} a postulé à votre offre '{instance.offre.titre}'.",
            url=f"/rh/candidatures/detail/{instance.id_candidature}/",
            related_candidature=instance
        )

@receiver(post_save, sender=Candidature)
def notify_candidature_status_change(sender, instance, **kwargs):
    """Notifier le candidat lorsque le statut de sa candidature change"""
    if instance.pk:
        try:
            old_instance = Candidature.objects.get(pk=instance.pk)
            if old_instance.statut != instance.statut:
                # Créer une notification pour le candidat
                messages = {
                    'en_revue': f"Votre candidature pour '{instance.offre.titre}' est en cours de revue.",
                    'retenue': f"🎉 Félicitations ! Votre candidature pour '{instance.offre.titre}' a été retenue !",
                    'convoque': f"Vous êtes convoqué pour un entretien pour l'offre '{instance.offre.titre}'.",
                    'embauche': f"🎊 Excellente nouvelle ! Vous avez été embauché pour '{instance.offre.titre}' !",
                    'rejetee': f"Votre candidature pour '{instance.offre.titre}' n'a pas été retenue.",
                }
                
                if instance.statut in messages:
                    Notification.objects.create(
                        user=instance.candidat,
                        type_notification='statut',
                        titre=f"Mise à jour de votre candidature",
                        message=messages[instance.statut],
                        url=f"/mes-candidatures/",
                        related_candidature=instance
                    )
        except Candidature.DoesNotExist:
            pass

@receiver(post_save, sender=User)
def notify_admin_new_user(sender, instance, created, **kwargs):
    """Notifier les administrateurs lorsqu'un nouvel utilisateur s'inscrit"""
    if created and not instance.is_superuser:
        # Notifier tous les administrateurs
        admins = User.objects.filter(Q(is_superuser=True) | Q(profile__role='admin'))
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                type_notification='system',
                titre='Nouvel utilisateur inscrit',
                message=f"L'utilisateur {instance.username} vient de s'inscrire sur la plateforme.",
                url=f"/admin/utilisateurs/{instance.id}/",
            )