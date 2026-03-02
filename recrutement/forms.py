# recrutement/forms.py - VERSION CORRIGÉE
from django import forms
from .models import Offre, Candidature
from django.utils import timezone
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Candidature
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils import timezone
from .models import Offre, Administration, Grade

from django import forms
from django.utils import timezone
from .models import Offre, Administration, UserProfile

class OffreForm(forms.ModelForm):
    # Surcharger le champ grade pour forcer les choix
    grade = forms.ChoiceField(
        choices=Offre.GRADE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Surcharger le champ salaire
    salaire = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': 0,
            'placeholder': 'Ex: 3000'
        })
    )
    
    class Meta:
        model = Offre
        fields = [
            'titre', 
            'description', 
            'administration', 
            'grade',  # Utilise le champ surchargé
            'date_limite', 
            'statut',
            'nombre_postes', 
            'salaire',  # Utilise le champ surchargé
            'type_contrat'
        ]
        
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Développeur Full Stack Senior'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez les missions, compétences requises et avantages...'
            }),
            'administration': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_limite': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nombre_postes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'type_contrat': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        # Extraire l'utilisateur si fourni
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les administrations en fonction de l'utilisateur
        if self.user:
            # Vérifier si l'utilisateur a un profil
            try:
                user_profile = self.user.profile
                # Si l'utilisateur a une administration spécifique
                if hasattr(user_profile, 'administration') and user_profile.administration:
                    # Limiter à l'administration de l'utilisateur
                    self.fields['administration'].queryset = Administration.objects.filter(id=user_profile.administration.id)
                    # Pré-sélectionner l'administration de l'utilisateur
                    self.fields['administration'].initial = user_profile.administration
                    # Rendre le champ en lecture seule si l'utilisateur n'a qu'une seule administration
                    self.fields['administration'].widget.attrs['disabled'] = True
                    # Ajouter l'ID comme champ caché pour que la valeur soit envoyée
                    self.fields['administration'].widget = forms.HiddenInput()
                    # Créer un champ d'affichage en lecture seule
                    self.readonly_administration = user_profile.administration
                # Si l'utilisateur a plusieurs administrations
                elif hasattr(user_profile, 'administrations') and user_profile.administrations.exists():
                    self.fields['administration'].queryset = user_profile.administrations.all()
            except (UserProfile.DoesNotExist, AttributeError):
                # Si pas de profil ou pas d'administration définie, afficher toutes les administrations
                self.fields['administration'].queryset = Administration.objects.all()
        else:
            # Si pas d'utilisateur, afficher toutes les administrations
            self.fields['administration'].queryset = Administration.objects.all()
        
        # Ajouter une option vide au début des choix de grade
        self.fields['grade'].choices = [('', '--- Sélectionnez un grade ---')] + list(self.fields['grade'].choices)[1:]
        
        # Ajout d'options vides pour les selects
        if 'empty_label' not in self.fields['administration'].widget.attrs:
            self.fields['administration'].empty_label = "Sélectionnez une administration"
        
        self.fields['statut'].empty_label = "Sélectionnez un statut"
        self.fields['type_contrat'].empty_label = "Sélectionnez un type de contrat"
        
        # Définir la date minimale pour date_limite
        today = timezone.now().date()
        self.fields['date_limite'].widget.attrs['min'] = today.strftime('%Y-%m-%d')
        
        # Définir la valeur par défaut pour le statut
        if not self.instance.pk:  # Si c'est une nouvelle offre
            self.fields['statut'].initial = 'ouverte'
    
    def clean_administration(self):
        """Nettoyer le champ administration en tenant compte de l'utilisateur"""
        if hasattr(self, 'user') and self.user:
            try:
                user_profile = self.user.profile
                # Si l'utilisateur a une seule administration, forcer cette valeur
                if hasattr(user_profile, 'administration') and user_profile.administration:
                    return user_profile.administration
            except (UserProfile.DoesNotExist, AttributeError):
                pass
        
        # Sinon, retourner la valeur normale
        administration = self.cleaned_data.get('administration')
        return administration
    
class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['cv', 'lettre_motivation', 'commentaire_candidat']
        widgets = {
            'commentaire_candidat': forms.Textarea(attrs={'rows': 3}),
        }

class UserUpdateForm(forms.ModelForm):
    """Formulaire pour mettre à jour les informations de base"""
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre email',
            'style': 'border-color: #00B4D8;'
        })
    )
    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom',
            'style': 'border-color: #00B4D8;'
        })
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom',
            'style': 'border-color: #00B4D8;'
        })
    )


    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UserProfileUpdateForm(forms.ModelForm):
    """Formulaire pour mettre à jour le profil étendu"""
    phone = forms.CharField(
        label="Téléphone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+212 6 XX XX XX XX',
            'style': 'border-color: #00B4D8;'
        })
    )
    address = forms.CharField(
        label="Adresse",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Votre adresse complète',
            'style': 'border-color: #00B4D8;'
        })
    )
    cv_default = forms.FileField(
        label="CV par défaut (PDF recommandé)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx',
            'style': 'border-color: #00B4D8;'
        })
    )
    profession = forms.CharField(
        label="Profession actuelle",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre profession',
            'style': 'border-color: #00B4D8;'
        })
    )
    experience = forms.IntegerField(
        label="Années d'expérience",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'style': 'border-color: #00B4D8;'
        })
    )
    niveau_etude = forms.ChoiceField(
        label="Niveau d'étude",
        choices=[
            ('', 'Sélectionnez votre niveau'),
            ('bac', 'Baccalauréat'),
            ('bac+2', 'Bac+2'),
            ('bac+3', 'Licence'),
            ('bac+5', 'Master'),
            ('doctorat', 'Doctorat'),
            ('autre', 'Autre'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'border-color: #00B4D8;'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'cv_default', 'profession', 'experience', 'niveau_etude']

class CustomUserCreationForm(UserCreationForm):
    # Définition des champs ADDITIONNELS (ceux qui ne sont pas dans User)
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    # MODIFICATION 1: Supprimer les clean_username et clean_email
    # OU les modifier pour qu'ils ne lèvent pas d'exception immédiatement
    
    def clean_username(self):
        """Vérifie que le username n'existe pas déjà mais ne bloque pas la validation"""
        username = self.cleaned_data.get('username')
        
        if username:
            # Vérifie si un utilisateur a déjà ce username
            if User.objects.filter(username__iexact=username).exists():
                # Ajoute l'erreur au champ sans bloquer le formulaire
                self.add_error('username', 
                    "Ce nom d'utilisateur est déjà utilisé. Veuillez en choisir un autre.")
        
        return username
    
    def clean_email(self):
        """Vérifie que l'email n'existe pas déjà mais ne bloque pas la validation"""
        email = self.cleaned_data.get('email')
        
        if email:
            # Normalise l'email
            email = email.lower().strip()
            
            # Vérifie si un utilisateur a déjà cet email
            if User.objects.filter(email__iexact=email).exists():
                # Ajoute l'erreur au champ sans lever d'exception
                self.add_error('email', 
                    "Cet email est déjà utilisé. Veuillez utiliser une autre adresse email.")
        
        return email
    
    # MODIFICATION 2: Ajouter une validation globale
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        
        # Vérifier à nouveau pour s'assurer que les erreurs sont bien ajoutées
        if username and User.objects.filter(username__iexact=username).exists():
            if 'username' not in self.errors:
                self.add_error('username', 
                    "Ce nom d'utilisateur est déjà utilisé. Veuillez en choisir un autre.")
        
        if email:
            email = email.lower().strip()
            if User.objects.filter(email__iexact=email).exists():
                if 'email' not in self.errors:
                    self.add_error('email', 
                        "Cet email est déjà utilisé. Veuillez utiliser une autre adresse email.")
        
        return cleaned_data
    

    def save(self, commit=True):
        # Save the user first
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower().strip()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            # Just save the user, nothing else
            user.save()
        
        # Create UserProfile ONLY if it doesn't exist
        from .models import UserProfile
        
    
        
        return user
class AdministrationForm(forms.ModelForm):
    class Meta:
        model = Administration
        fields = ['nom', 'ville', 'type_administration', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Ministère de l\'Éducation',
                'autofocus': True
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Rabat'
            }),
            'type_administration': forms.Select(attrs={
                'class': 'form-select'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
        }
        labels = {
            'nom': 'Nom de l\'administration',
            'ville': 'Ville',
            'type_administration': 'Type d\'administration',
            'adresse': 'Adresse complète',
        }
    