from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

from django.db import models
from django.contrib.auth.models import User
import os



# Évitez d'importer des vues ou d'autres modules qui pourraient créer des circulaires
def cv_upload_path(instance, filename):
    return f'cvs/{instance.candidat.username}/{instance.offre.id}/{filename}'

def lettre_upload_path(instance, filename):
    return f'lettres/{instance.candidat.username}/{instance.offre.id}/{filename}'

class Administration(models.Model):
    TYPE_CHOICES = [
        ('ministere', 'Ministère'),
        ('agence', 'Agence'),
        ('collectivite', 'Collectivité territoriale'),
        ('etablissement', 'Établisssement public'),
        ('autre', 'Autre'),
    ]
    
    id_administration = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=200, verbose_name="Nom de l'administration")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    type_administration = models.CharField(
        max_length=50, 
        choices=TYPE_CHOICES, 
        verbose_name="Type d'administration"
    )
    adresse = models.TextField(verbose_name="Adresse complète", blank=True)
    
    class Meta:
        verbose_name = "Administration"
        verbose_name_plural = "Administrations"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} - {self.ville}"

class Adresse(models.Model):
    id_adresse = models.AutoField(primary_key=True)
    candidat = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='adresses',
        null=True,
        blank=True
    )
    pays = models.CharField(max_length=100, verbose_name="Pays", default="Madagascar")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    rue = models.CharField(max_length=200, verbose_name="Rue")
    complement_adresse = models.TextField(verbose_name="Complément d'adresse", blank=True)
    code_postal = models.CharField(max_length=20, verbose_name="Code postal", blank=True)
    
    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
    
    def __str__(self):
        return f"{self.rue}, {self.ville}, {self.pays}"
    
class Grade(models.Model):
    nom = models.CharField(max_length=200)
    niveau = models.CharField(max_length=50, blank=True)
    # ... autres champs
    
    def __str__(self):
        return f"{self.nom} ({self.niveau})" if self.niveau else self.nom
    
class Offre(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publiee', 'Publiée'),
        ('pourvue', 'Pourvue'),
        ('expiree', 'Expirée'),
    ]
    
    GRADE_CHOICES = [
        ('grade1', 'Grade 1'),
        ('grade2', 'Grade 2'),
        ('grade3', 'Grade 3'),
        ('grade4', 'Grade 4'),
        ('grade5', 'Grade 5'),
    ]
    
    id_offre = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=200, verbose_name="Titre du poste")
    description = models.TextField(verbose_name="Description détaillée")
    date_limite = models.DateField(verbose_name="Date limite de candidature")
    grade = models.CharField(
        max_length=20, 
        choices=GRADE_CHOICES, 
        verbose_name="Grade"
    )
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='brouillon',
        verbose_name="Statut de l'offre"
    )
    
    administration = models.ForeignKey(
        Administration, 
        on_delete=models.CASCADE, 
        verbose_name="Administration",
        related_name='offres'
    )
    createur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Créateur (RH)",
        related_name='offres_crees',
        null=True,
        blank=True
    )
    
    date_publication = models.DateField(
        auto_now_add=True, 
        verbose_name="Date de publication"
    )
    nombre_postes = models.PositiveIntegerField(
        default=1, 
        verbose_name="Nombre de postes disponibles"
    )
    salaire = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Salaire mensuel", 
        null=True, 
        blank=True
    )
    type_contrat = models.CharField(
        max_length=50, 
        default='CDD', 
        verbose_name="Type de contrat",
        choices=[
            ('CDD', 'Contrat à durée déterminée'),
            ('CDI', 'Contrat à durée indéterminée'),
            ('stage', 'Stage'),
            ('freelance', 'Freelance'),
        ]
    )
    
    class Meta:
        verbose_name = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"
        ordering = ['-date_publication']
    
    def __str__(self):
        return f"{self.titre} - {self.administration.nom}"
    
    @property
    def est_expiree(self):
        return timezone.now().date() > self.date_limite
    
    @property
    def jours_restants(self):
        delta = self.date_limite - timezone.now().date()
        return delta.days if delta.days > 0 else 0
    
    # Méthode pour obtenir le label du grade
    @property  
    def get_grade_display_name(self):
        for value, label in self.GRADE_CHOICES:
            if value == self.grade:
                return label
        return f"Grade {self.grade}"

class CandidatProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    telephone = models.CharField(max_length=20, verbose_name="Téléphone", blank=True)
    date_inscription = models.DateField(
        auto_now_add=True, 
        verbose_name="Date d'inscription"
    )
    
    profession = models.CharField(max_length=100, verbose_name="Profession actuelle", blank=True)
    experience = models.PositiveIntegerField(
        verbose_name="Années d'expérience", 
        default=0
    )
    niveau_etude = models.CharField(
        max_length=100, 
        verbose_name="Niveau d'étude", 
        blank=True,
        choices=[
            ('bac', 'Baccalauréat'),
            ('bac+2', 'Bac+2'),
            ('bac+3', 'Licence'),
            ('bac+5', 'Master'),
            ('doctorat', 'Doctorat'),
        ]
    )
    
    cv_default = models.FileField(
        upload_to='cvs/default/%Y/%m/', 
        verbose_name="CV par défaut",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Profil candidat"
        verbose_name_plural = "Profils candidats"
    
    def __str__(self):
        return f"Profil de {self.user.get_full_name() or self.user.username}"

class Candidature(models.Model):
    STATUT_CHOICES = [
        ('deposee', 'Déposée'),
        ('en_revue', 'En revue'),
        ('retenue', 'Retenue'),
        ('rejetee', 'Rejetée'),
        ('convoque', 'Convoqué'),
        ('embauche', 'Embauché'),
    ]
    
    id_candidature = models.AutoField(primary_key=True)
    candidat = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Candidat",
        related_name='candidatures'
    )
    offre = models.ForeignKey(
        Offre, 
        on_delete=models.CASCADE, 
        verbose_name="Offre",
        related_name='candidatures'
    )
    
    date_depot = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de dépôt"
    )
    date_validation = models.DateField(
        verbose_name="Date de validation", 
        null=True, 
        blank=True
    )
    delai_reponse = models.DateField(
        verbose_name="Délai de réponse", 
        null=True, 
        blank=True
    )
    
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='deposee',
        verbose_name="Statut de la candidature"
    )
    
    cv = models.FileField(
        upload_to=cv_upload_path,
        verbose_name="Curriculum Vitae",
        null=True,
        blank=True
    )
    lettre_motivation = models.FileField(
        upload_to=lettre_upload_path,
        verbose_name="Lettre de motivation",
        blank=True,
        null=True
    )
    
    commentaire_rh = models.TextField(
        verbose_name="Commentaire du RH", 
        blank=True
    )
    commentaire_candidat = models.TextField(
        verbose_name="Commentaire du candidat", 
        blank=True
    )
    
    valide = models.BooleanField(
        default=False, 
        verbose_name="Candidature validée"
    )
    
    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        unique_together = ['candidat', 'offre']
        ordering = ['-date_depot']
    
    def __str__(self):
        return f"{self.candidat.username} - {self.offre.titre} ({self.statut})"
    
    def get_cv_filename(self):
        return os.path.basename(self.cv.name) if self.cv else "Non fourni"
    
    def get_lettre_filename(self):
        if self.lettre_motivation:
            return os.path.basename(self.lettre_motivation.name)
        return "Non fournie"

class AdministrateurRH(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    id_RH = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="ID RH"
    )
    telephone = models.CharField(max_length=20, verbose_name="Téléphone", blank=True)
    administration = models.ForeignKey(
        Administration, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Administration rattachée",
        related_name='administrateurs_rh'
    )
    date_embauche = models.DateField(
        verbose_name="Date d'embauche", 
        null=True, 
        blank=True
    )
    
    peut_valider = models.BooleanField(
        default=True, 
        verbose_name="Peut valider les candidatures"
    )
    peut_publier = models.BooleanField(
        default=True, 
        verbose_name="Peut publier des offres"
    )
    
    class Meta:
        verbose_name = "Administrateur RH"
        verbose_name_plural = "Administrateurs RH"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.id_RH}"

class SuperAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    date_nomination = models.DateField(
        auto_now_add=True, 
        verbose_name="Date de nomination"
    )
    
    class Meta:
        verbose_name = "Super Administrateur"
        verbose_name_plural = "Super Administrateurs"
    
    def __str__(self):
        return f"SuperAdmin: {self.user.username}"

class CandidatFavoris(models.Model):
    candidat = models.ForeignKey(User, on_delete=models.CASCADE)
    offre = models.ForeignKey(Offre, on_delete=models.CASCADE)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['candidat', 'offre']
        verbose_name = "Offre favorite"
        verbose_name_plural = "Offres favorites"
    
    def __str__(self):
        return f"{self.candidat.username} - {self.offre.titre}"
    
class UserProfile(models.Model):
    """Profil utilisateur étendu (pour tous les utilisateurs)"""
    ROLE_CHOICES = [
    ('candidat', 'Candidat'),
    ('rh', 'Ressources Humaines'),
    ('admin', 'Administrateur'),
    ('superadmin', 'Super Administrateur'),
]

    # Rôle de connexion (pour basculer entre interfaces)
    SELECTED_ROLE_CHOICES = [
    ('user', 'Utilisateur Normal'),
    ('rh', 'Ressources Humaines'),
    ('superadmin', 'Super Administrateur'),
]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile',)
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    country = models.CharField(max_length=100, blank=True, verbose_name="Pays", default="FR")
    
    # Champs de rôle
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='candidat',
        verbose_name="Rôle dans le système"
    )
    
    selected_role = models.CharField(
        max_length=10, 
        choices=SELECTED_ROLE_CHOICES, 
        default='user',
        verbose_name="Rôle de connexion"
    )
    
    # Pour les candidats
    cv_default = models.FileField(
        upload_to='cvs/default/%Y/%m/', 
        verbose_name="CV par défaut",
        blank=True,
        null=True
    )
    
    cv_upload_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de téléchargement du CV")
    
    cover_letter = models.FileField(
        upload_to='cover_letters/%Y/%m/',
        verbose_name="Lettre de motivation",
        blank=True,
        null=True
    )
    
    # Informations supplémentaires
    profession = models.CharField(max_length=100, verbose_name="Profession actuelle", blank=True)
    experience = models.PositiveIntegerField(
        verbose_name="Années d'expérience", 
        default=0
    )
    niveau_etude = models.CharField(
        max_length=100, 
        verbose_name="Niveau d'étude", 
        blank=True,
        choices=[
            ('bac', 'Baccalauréat'),
            ('bac+2', 'Bac+2'),
            ('bac+3', 'Licence'),
            ('bac+5', 'Master'),
            ('doctorat', 'Doctorat'),
            ('autre', 'Autre'),
        ]
    )
    
    # Date de création/mise à jour
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    def has_cv(self):
        """Vérifie si l'utilisateur a un CV"""
        return bool(self.cv_default)
    
    def get_cv_filename(self):
        """Retourne le nom du fichier CV"""
        if self.cv_default:
            return os.path.basename(self.cv_default.name)
        return "Aucun CV"
    
    def can_switch_role(self):
        """Vérifie si l'utilisateur peut changer de rôle"""
        return self.role in ['rh', 'admin'] or self.user.is_superuser or self.user.is_staff
    
    def get_display_role(self):
        """Retourne le rôle affiché"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def get_display_selected_role(self):
        """Retourne le rôle de connexion affiché"""
        return dict(self.SELECTED_ROLE_CHOICES).get(self.selected_role, self.selected_role)
    
    # Pour la compatibilité avec CandidatProfile existant
    @property
    def date_inscription(self):
        return self.user.date_joined.date()
    
    @property
    def is_rh_user(self):
        """Vérifie si l'utilisateur est un RH"""
        return self.role == 'rh' or self.user.is_staff or self.user.is_superuser


class Notification(models.Model):
    TYPE_CHOICES = [
        ('offre', 'Nouvelle Offre'),
        ('candidature', 'Candidature'),
        ('statut', 'Changement de Statut'),
        ('message', 'Message'),
        ('system', 'Système'),
    ]
    
    id_notification = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    url = models.URLField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    related_offre = models.ForeignKey(Offre, on_delete=models.CASCADE, null=True, blank=True)
    related_candidature = models.ForeignKey(Candidature, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.user.username}"
    
    @property
    def time_since(self):
        """Retourne le temps écoulé depuis la création"""
        now = timezone.now()
        diff = now - self.date_creation
        
        if diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"


# Signaux pour créer automatiquement le profil
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le UserProfile quand le User est sauvegardé"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


       