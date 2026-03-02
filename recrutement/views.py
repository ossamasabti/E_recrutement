from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Offre, Administration, Candidature
from .forms import OffreForm, AdministrationForm
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.http import JsonResponse
import json
from django.db.models import Q
from datetime import timedelta
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
import csv
from datetime import datetime
from django.contrib.auth.models import User 
from .models import UserProfile, Candidature
from .models import Notification
from django.views.decorators.http import require_POST

# recrutement/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate

from django.http import JsonResponse

# Importez vos modèles locaux
from .models import Offre, Administration, Candidature, Notification

# Vérification super admin
def is_superadmin(user):
    return user.is_authenticated and user.is_superuser

@login_required
def profile_view(request):
    """Page de profil"""
    # Récupérer les statistiques des candidatures de l'utilisateur
    candidatures = Candidature.objects.filter(candidat=request.user)
    
    # Compter les différentes catégories
    stats_candidatures = {
        'total': candidatures.count(),
        'en_cours': candidatures.filter(
            statut__in=['deposee', 'en_revue', 'retenue', 'convoque']
        ).count(),
        'acceptees': candidatures.filter(statut='retenue').count(),
        'rejetees': candidatures.filter(statut='rejetee').count(),
        'en_attente': candidatures.filter(statut='deposee').count(),
        'en_revue': candidatures.filter(statut='en_revue').count(),
        'convoques': candidatures.filter(statut='convoque').count(),
    }
    
    # Récupérer le profil utilisateur s'il existe
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        from .models import UserProfile
        profile = UserProfile.objects.create(user=request.user)
    
    return render(request, 'recrutement/profile.html', {
        'user': request.user,
        'profile': profile,
        'stats_candidatures': stats_candidatures,  # Nouvelle variable ajoutée
    })
# Vos fonctions de vue...
# Vérifie si l'utilisateur est staff/admin
def is_staff_user(user):
    return user.is_staff

# Vérifier si l'utilisateur a le droit d'accéder aux pages RH
def rh_access_required(view_func):
    """Décorateur pour restreindre l'accès aux utilisateurs RH avec le rôle sélectionné"""
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            return redirect('login')
        
        # Vérifier si l'utilisateur a un profil
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            from .models import UserProfile
            profile = UserProfile.objects.create(user=user)
        
        # Vérifier les droits RH
        # L'utilisateur doit avoir le rôle 'rh' dans son profil ET avoir sélectionné le rôle 'rh'
        if not (profile.role == 'rh' or user.is_superuser or user.is_staff):
            messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
            return redirect('profile')
        
        # Vérifier que l'utilisateur a sélectionné le rôle RH
        if profile.selected_role != 'rh':
            messages.warning(request, 
                "Vous êtes actuellement connecté en tant qu'utilisateur normal. "
                "Veuillez changer de rôle dans votre profil pour accéder aux fonctionnalités RH.")
            return redirect('profile')
        
        return view_func(request, *args, **kwargs)
    return wrapper

# ==================== PAGES PUBLIQUES ====================

def home(request):
    """Page d'accueil"""
    offres_recentes = Offre.objects.filter(
        statut='publiee',
        date_limite__gte=timezone.now().date()
    ).order_by('-date_publication')[:5]

    # Calculer le nombre d'administrations
    nombre_administrations = Administration.objects.count()

    context = {
        'offres_recentes': offres_recentes,
        'total_offres': Offre.objects.filter(statut='publiee').count(),
        'nombre_administrations': nombre_administrations,  # Nouvelle variable ajoutée
    }
    return render(request, 'recrutement/home.html', context)

def liste_offres(request):
    """Liste toutes les offres avec filtres et recherche"""
    # Récupérer tous les paramètres GET
    q = request.GET.get('q', '').strip()
    administration_id = request.GET.get('administration')
    grade = request.GET.get('grade')
    type_contrat = request.GET.get('type_contrat')
    statut = request.GET.get('statut')
    localisation = request.GET.get('localisation', '').strip()
    date_limite_filter = request.GET.get('date_limite')
    tri = request.GET.get('tri', 'date_desc')
    
    # Date d'aujourd'hui
    aujourd_hui = timezone.now().date()
    
    # Base queryset - seulement les offres publiées
    offres_list = Offre.objects.filter(statut='publiee')
    
    # Recherche textuelle
    if q:
        offres_list = offres_list.filter(
            Q(titre__icontains=q) |
            Q(description__icontains=q) |
            Q(administration__nom__icontains=q)
        )
    
    # Filtre administration
    if administration_id:
        offres_list = offres_list.filter(administration_id=administration_id)
    
    # Filtre grade
    if grade:
        offres_list = offres_list.filter(grade=grade)
    
    # Filtre type de contrat
    if type_contrat:
        offres_list = offres_list.filter(type_contrat=type_contrat)
    
    # Filtre localisation
    if localisation:
        offres_list = offres_list.filter(
            Q(administration__ville__icontains=localisation) |
            Q(administration__region__icontains=localisation)
        )
    
    # Filtre date limite
    if date_limite_filter:
        if date_limite_filter == '7jours':
            date_limite_min = aujourd_hui
            date_limite_max = aujourd_hui + timedelta(days=7)
            offres_list = offres_list.filter(
                date_limite__gte=date_limite_min,
                date_limite__lte=date_limite_max
            )
        elif date_limite_filter == '30jours':
            date_limite_min = aujourd_hui
            date_limite_max = aujourd_hui + timedelta(days=30)
            offres_list = offres_list.filter(
                date_limite__gte=date_limite_min,
                date_limite__lte=date_limite_max
            )
        elif date_limite_filter == 'expiree':
            offres_list = offres_list.filter(date_limite__lt=aujourd_hui)
    
    # Filtre statut - par défaut on montre seulement les non expirées
    # sauf si l'utilisateur choisit explicitement "expiree"
    if not date_limite_filter:  # Si pas de filtre date, montrer seulement les non expirées
        offres_list = offres_list.filter(date_limite__gte=aujourd_hui)
    
    # Trier les résultats
    if tri == 'date_asc':
        offres_list = offres_list.order_by('date_publication')
    elif tri == 'date_limite_asc':
        offres_list = offres_list.order_by('date_limite')
    elif tri == 'titre_asc':
        offres_list = offres_list.order_by('titre')
    else:  # date_desc par défaut
        offres_list = offres_list.order_by('-date_publication')
    
    # Pagination
    paginator = Paginator(offres_list, 10)
    page_number = request.GET.get('page')
    offres = paginator.get_page(page_number)
    
    # Préparer le contexte
    administrations = Administration.objects.all()
    selected_administration = None
    if administration_id:
        try:
            selected_administration = Administration.objects.get(id=administration_id)
        except Administration.DoesNotExist:
            pass
    
    # Déterminer si des filtres sont actifs
    has_filters = any([
        q,
        administration_id,
        grade,
        type_contrat,
        statut,
        localisation,
        date_limite_filter,
        tri != 'date_desc'
    ])
    
    context = {
        'offres': offres,
        'administrations': administrations,
        'grade_choices': Offre.GRADE_CHOICES,
        'contrat_choices': Offre.type_contrat,
        'statut_choices': Offre.STATUT_CHOICES,
        'selected_administration': selected_administration,
        'selected_grade_label': dict(Offre.GRADE_CHOICES).get(grade, '') if grade else '',
        'has_filters': has_filters,
        'request': request,  # Important pour réutiliser les paramètres GET dans le template
    }
    
    return render(request, 'recrutement/offres/liste.html', context)

def detail_offre(request, offre_id):
    """Détail d'une offre"""
    offre = get_object_or_404(Offre, pk=offre_id, statut='publiee')
    
    # Vérifier si l'utilisateur connecté a déjà postulé
    a_postule = False
    if request.user.is_authenticated:
        a_postule = Candidature.objects.filter(
            candidat=request.user, 
            offre=offre
        ).exists()
    
    context = {
        'offre': offre,
        'a_postule': a_postule,
        'jours_restants': offre.jours_restants,
    }
    return render(request, 'recrutement/offres/detail.html', context)

def about(request):
    """Page À propos / About Us"""
    context = {
        'title': 'À propos de nous',
        'page_description': 'Découvrez MADA JOBINCLICK, notre mission et notre équipe',
    }
    return render(request, 'recrutement/about.html', context)

def login_view(request):
    """Connexion utilisateur"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {username}!')
                return redirect('home')
        messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = AuthenticationForm()
    return render(request, 'recrutement/login.html', {'form': form})

def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')


def register_view(request):
    """Inscription"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # This will create both User and UserProfile
                user = form.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, 'Votre compte a été créé avec succès!')
                return redirect('profile')
                
            except Exception as e:
                # If error, show message but keep form data
                messages.error(request, f'Erreur: {str(e)}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'recrutement/register.html', {'form': form})
# ==================== PROFIL UTILISATEUR ====================

@login_required
def edit_profile(request):
    """Vue pour modifier le profil utilisateur"""
    user = request.user
    
    # Essayer de récupérer le profil ou le créer s'il n'existe pas
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        from .models import UserProfile
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        try:
            # Mettre à jour les informations de l'utilisateur
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.save()
            
            # Mettre à jour le profil avec les nouveaux champs
            profile.phone = request.POST.get('phone', profile.phone)
            profile.address = request.POST.get('address', profile.address)
            profile.postal_code = request.POST.get('postal_code', profile.postal_code)
            profile.city = request.POST.get('city', profile.city)
            profile.country = request.POST.get('country', profile.country or 'FR')
            
            # Nouvaux champs ajoutés
            profile.profession = request.POST.get('profession', profile.profession)
            profile.niveau_etude = request.POST.get('niveau_etude', profile.niveau_etude)
            
            # Gérer l'expérience (conversion en entier sécurisée)
            experience_str = request.POST.get('experience', '')
            if experience_str:
                try:
                    profile.experience = int(experience_str)
                except (ValueError, TypeError):
                    profile.experience = 0
            else:
                # Si le champ est vide, mettre 0
                profile.experience = 0
            
            # Gestion du CV
            if 'cv' in request.FILES:
                # Supprimer l'ancien CV s'il existe
                if profile.cv_default:
                    profile.cv_default.delete(save=False)
                
                profile.cv_default = request.FILES['cv']
                profile.cv_upload_date = timezone.now()
                
            # Gestion de la lettre de motivation
            if 'cover_letter' in request.FILES:
                # Supprimer l'ancienne lettre de motivation si elle existe
                if profile.cover_letter:
                    profile.cover_letter.delete(save=False)
                    
                profile.cover_letter = request.FILES['cover_letter']
            
            # Gestion du rôle de connexion selon le type d'utilisateur

            # 1. SUPER ADMIN SEUL (is_superuser = True)
            if user.is_superuser:
                # Le super admin peut choisir n'importe quel rôle
                selected_role = request.POST.get('selected_role')
                if selected_role in ['user', 'rh', 'superadmin']:
                    profile.selected_role = selected_role
                else:
                    # Par défaut pour super admin
                    profile.selected_role = 'superadmin'

            # 2. RH SEUL (profile.role = 'rh' ET user.is_staff = True)
            elif profile.role == 'rh' and user.is_staff:
                # Le RH peut choisir entre 'user' et 'rh'
                selected_role = request.POST.get('selected_role')
                if selected_role in ['user', 'rh']:
                    profile.selected_role = selected_role
                else:
                    # Par défaut pour RH
                    profile.selected_role = 'rh'

            # 3. ADMIN SEUL (profile.role = 'admin' ET user.is_staff = True)
            elif profile.role == 'admin' and user.is_staff:
                # L'admin peut choisir entre 'user', 'rh', et 'admin' (si présent dans les choix)
                selected_role = request.POST.get('selected_role')
                if selected_role in ['user', 'rh', 'admin']:
                    profile.selected_role = selected_role
                else:
                    # Par défaut pour admin
                    profile.selected_role = 'rh'  # ou 'admin' selon votre logique

            # 4. USER NORMAL SEUL (candidat)
            elif profile.role == 'candidat':
                # L'utilisateur normal ne peut choisir que 'user'
                profile.selected_role = 'user'

            # 5. CAS FALLBACK (pour sécurité)
            else:
                # Si rien ne correspond, forcer le rôle 'user'
                profile.selected_role = 'user'

            profile.save()

            # Vérification des droits avant redirection
            if profile.selected_role == 'rh':
                # Vérifier si l'utilisateur a réellement le droit d'être RH
                if profile.role == 'rh' or user.is_superuser or user.is_staff:
                    return redirect('profile')
                else:
                    # Si l'utilisateur n'est pas vraiment RH, forcer le rôle user
                    profile.selected_role = 'user'
                    profile.save()
                    messages.warning(request, "Vous n'avez pas les droits pour accéder au tableau de bord RH.")
                    return redirect('profile')
            else:
                return redirect('profile')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
            # Afficher l'erreur dans la console pour le débogage
            print(f"Erreur lors de la mise à jour du profil: {e}")
    
    # Préparer le contexte pour le template
    context = {
        'user': user,
    }
    
    return render(request, 'recrutement/edit_profile.html', context)
# ==================== CANDIDATURES ====================

@login_required
def postuler(request, offre_id):
    """Postuler à une offre"""
    offre = get_object_or_404(Offre, id_offre=offre_id, statut='publiee')
    
    # Vérifications
    if offre.est_expiree:
        messages.error(request, 'Cette offre est expirée.')
        return redirect('detail_offre', offre_id=offre_id)
    
    if Candidature.objects.filter(candidat=request.user, offre=offre).exists():
        messages.warning(request, 'Vous avez déjà postulé à cette offre.')
        return redirect('detail_offre', offre_id=offre_id)
    
    # Créer la candidature (uniquement sur POST)
    if request.method == 'POST':
        Candidature.objects.create(
            candidat=request.user,
            offre=offre,
            statut='deposee'
        )
        
        messages.success(request, 'Votre candidature a été envoyée avec succès!')
        return redirect('detail_offre', offre_id=offre_id)
    
    return redirect('detail_offre', offre_id=offre_id)

@login_required
def mes_candidatures(request):
    """Vue pour afficher les candidatures de l'utilisateur connecté"""
    candidatures = Candidature.objects.filter(
        candidat=request.user
    ).select_related('offre', 'offre__administration').order_by('-date_depot')
    
    # Compter les statuts pour les statistiques
    stats = {
        'total': candidatures.count(),
        'en_revue': candidatures.filter(statut='en_revue').count(),
        'retenues': candidatures.filter(statut='retenue').count(),
        'rejetees': candidatures.filter(statut='rejetee').count(),
        'convoques': candidatures.filter(statut='convoque').count(),
        'embauches': candidatures.filter(statut='embauche').count(),
        'deposees': candidatures.filter(statut='deposee').count(),
    }
    
    context = {
        'candidatures': candidatures,
        'stats': stats,
        'active_page': 'mes_candidatures',
    }
    
    return render(request, 'recrutement/mes_candidatures.html', context)

@login_required
def annuler_candidature(request, candidature_id):
    """Vue pour annuler une candidature"""
    candidature = get_object_or_404(Candidature, id_candidature=candidature_id, candidat=request.user)
    
    if candidature.candidat != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect('mes_candidatures')
    
    if candidature.statut != 'deposee':
        messages.warning(request, "Vous ne pouvez annuler que les candidatures au statut 'Déposée'.")
        return redirect('mes_candidatures')
    
    if request.method == 'POST':
        candidature.delete()
        messages.success(request, "Votre candidature a été annulée avec succès.")
        return redirect('mes_candidatures')
    
    return render(request, 'recrutement/confirmation_annulation.html', {
        'candidature': candidature,
        'active_page': 'mes_candidatures',
    })

# ==================== TABLEAU DE BORD ADMIN ====================

@login_required
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """Tableau de bord d'administration"""

    stats = {
        'total_offres': Offre.objects.count(),
        'offres_actives': Offre.objects.filter(statut='publiee').count(),
        'total_candidatures': Candidature.objects.count(),
        'nombre_administrations':Administration.objects.count(),
        'total_users' :User.objects.count()
    }

    recent_offres = Offre.objects.all().order_by('-date_publication')[:10]
    
    context = {
        'stats': stats,
        'recent_offres': recent_offres,
        'current_date': timezone.now(),
        'user': request.user,
        'active_page': 'admin_dashboard',
    }
    
    return render(request, 'recrutement/admin_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def admin_liste_offres(request):
    """Liste des offres pour l'admin (ancienne interface)"""
    offres_list = Offre.objects.filter(createur=request.user).order_by('-date_publication')
    
    paginator = Paginator(offres_list, 10)
    page_number = request.GET.get('page')
    offres = paginator.get_page(page_number)
    
    context = {
        'offres': offres,
        'total_offres': offres_list.count(),
        'offres_publiees': offres_list.filter(statut='publiee').count(),
        'offres_brouillon': offres_list.filter(statut='brouillon').count(),
    }
    return render(request, 'recrutement/offres/admin_liste.html', context)



# ==================== NOUVELLE INTERFACE GESTION DES OFFRES ====================
@login_required
@rh_access_required
def gestion_offres(request):
    """Page principale de gestion des offres (nouvelle interface) - Seulement les offres publiées par l'utilisateur"""
    # Filtrer les offres pour n'afficher que celles créées par l'utilisateur connecté
    offres = Offre.objects.filter(createur=request.user).order_by('-date_publication')
    administrations = Administration.objects.all()
    
    # Préparer les données pour le template
    offres_data = []
    for offre in offres:
        offres_data.append({
            'id': offre.id_offre,
            'title': offre.titre,
            'admin': offre.administration.nom,
            'status': offre.statut,
            'deadline': offre.date_limite.isoformat() if offre.date_limite else None,
            'description': offre.description,
            'contract': offre.type_contrat,
            'createur': offre.createur.username  # Ajouter l'information du créateur
        })
    
    # Convertir en JSON
    offres_json = json.dumps(offres_data)
    
    # Statistiques pour le tableau de bord
    total_offres = offres.count()
    offres_actives = offres.filter(statut='ouverte').count()
    offres_fermees = offres.filter(statut='fermee').count()
    offres_pourvues = offres.filter(statut='pourvue').count()
    
    context = {
        'offres_json': offres_json,
        'administrations': administrations,
        'total_offres': total_offres,
        'offres_actives': offres_actives,
        'offres_fermees': offres_fermees,
        'offres_pourvues': offres_pourvues,
    }
    
    return render(request, 'recrutement/gestion_offres.html', context)

@login_required
@rh_access_required
def nouvelle_offre(request):
    # Si l'utilisateur RH a une administration spécifique associée
    # Vous devez avoir un modèle UserProfile ou une relation pour cela
    user_profile = getattr(request.user, 'profile', None)
    
    if request.method == 'POST':
        print("=== DEBUG: Données POST reçues ===")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")
        
        form = OffreForm(request.POST)
        
        if form.is_valid():
            # DEBUG: Afficher les données nettoyées
            print("=== DEBUG: Données nettoyées ===")
            print(f"  Grade: {form.cleaned_data.get('grade')}")
            print(f"  Salaire: {form.cleaned_data.get('salaire')}")
            
            offre = form.save(commit=False)
            offre.createur = request.user
            
            # DEBUG avant sauvegarde
            print("=== DEBUG: Avant sauvegarde ===")
            print(f"  Offre.grade: {offre.grade}")
            print(f"  Offre.salaire: {offre.salaire}")
            
            offre.save()
            
            # DEBUG après sauvegarde
            print("=== DEBUG: Après sauvegarde ===")
            print(f"  ID: {offre.id_offre}")
            print(f"  Grade en DB: {offre.grade}")
            print(f"  Salaire en DB: {offre.salaire}")
            
            messages.success(request, 'Offre créée avec succès !')
            return redirect('gestion_offres')
        else:
            print("=== DEBUG: Erreurs du formulaire ===")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = OffreForm()
    
    # Si vous voulez limiter les administrations que l'utilisateur peut choisir
    # Par exemple, si chaque utilisateur RH est associé à une administration
    if user_profile and hasattr(user_profile, 'administration'):
        # Limiter aux administrations de l'utilisateur
        administrations = [user_profile.administration]
    else:
        # Sinon, afficher toutes (ou selon la logique métier)
        administrations = Administration.objects.all()
    
    return render(request, 'recrutement/nouvelle_offre.html', {
        'form': form,
        'administrations': administrations,
    })
# ==================== API VIEWS ====================

def user_can_modify_offre(user, offre):
    """Vérifie si l'utilisateur peut modifier/supprimer une offre"""
    # Superadmin peut tout faire
    if user.is_superuser:
        return True
    
    # RH peut modifier/supprimer seulement s'il est le créateur
    if hasattr(offre, 'createur') and offre.createur == user:
        return True
    
    # Optionnel: vérifier si l'utilisateur a un rôle admin dans son profil
    try:
        if hasattr(user, 'profile') and hasattr(user.profile, 'role'):
            if user.profile.role in ['admin', 'superadmin']:
                return True
    except AttributeError:
        pass
    
    return False

@login_required
@rh_access_required
def get_offres_json(request):
    """Récupérer toutes les offres en JSON"""
    # Filtrer par créateur si l'utilisateur n'est pas superadmin
    if request.user.is_superuser:
        offres = Offre.objects.all()
    else:
        # Pour les RH, ne montrer que leurs propres offres
        offres = Offre.objects.filter(createur=request.user)
    
    offres = offres.order_by('-date_publication')
    
    offres_data = []
    for offre in offres:
        offres_data.append({
            'id': offre.id_offre,
            'title': offre.titre,
            'admin': offre.administration.nom,
            'status': offre.statut,
            'deadline': offre.date_limite.isoformat() if offre.date_limite else None,
            'description': offre.description,
            'contract': offre.type_contrat,
            'createur_id': offre.createur.id if offre.createur else None,
            'can_modify': user_can_modify_offre(request.user, offre)
        })
    
    return JsonResponse(offres_data, safe=False)

@login_required
@user_passes_test(is_staff_user)
def get_offre_detail_json(request, offre_id):
    """Récupérer une offre spécifique en JSON"""
    try:
        offre = Offre.objects.get(id_offre=offre_id)
        data = {
            'id': offre.id_offre,
            'titre': offre.titre,
            'administration_id': offre.administration.id_administration,
            'description': offre.description,
            'date_limite': offre.date_limite.isoformat() if offre.date_limite else None,
            'statut': offre.statut,
            'type_contrat': offre.type_contrat
        }
        return JsonResponse(data)
    except Offre.DoesNotExist:
        return JsonResponse({'error': 'Offre non trouvée'}, status=404)

@login_required
@user_passes_test(is_staff_user)
def create_offre_api(request):
    """Créer une nouvelle offre via API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validation
            if not all([data.get('titre'), data.get('administration_id'), data.get('description')]):
                return JsonResponse({'error': 'Champs obligatoires manquants'}, status=400)
            
            # Créer l'offre
            offre = Offre.objects.create(
                titre=data['titre'],
                administration_id=data['administration_id'],
                description=data['description'],
                date_limite=data.get('date_limite'),
                statut=data.get('statut', 'brouillon'),
                type_contrat=data.get('type_contrat', 'CDI'),
                createur=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Offre créée avec succès',
                'id': offre.id_offre
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
@user_passes_test(is_staff_user)
def update_offre_api(request, offre_id):
    """Mettre à jour une offre via API"""
    if request.method == 'POST':
        try:
            offre = Offre.objects.get(id_offre=offre_id)
            data = json.loads(request.body)
            
            # Mettre à jour les champs
            if 'titre' in data:
                offre.titre = data['titre']
            if 'administration_id' in data:
                offre.administration_id = data['administration_id']
            if 'description' in data:
                offre.description = data['description']
            if 'date_limite' in data:
                offre.date_limite = data['date_limite']
            if 'statut' in data:
                offre.statut = data['statut']
            if 'type_contrat' in data:
                offre.type_contrat = data['type_contrat']
            
            offre.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Offre mise à jour avec succès'
            })
            
        except Offre.DoesNotExist:
            return JsonResponse({'error': 'Offre non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
@user_passes_test(is_staff_user)
def delete_offre_api(request, offre_id):
    """Supprimer une offre via API"""
    if request.method == 'POST':
        try:
            offre = Offre.objects.get(id_offre=offre_id)
            titre = offre.titre
            offre.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Offre "{titre}" supprimée avec succès'
            })
            
        except Offre.DoesNotExist:
            return JsonResponse({'error': 'Offre non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
@rh_access_required
def bulk_action_api(request):
    """Actions groupées sur plusieurs offres"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            offre_ids = data.get('offre_ids', [])
            action = data.get('action', '')
            
            if not offre_ids:
                return JsonResponse({'error': 'Aucune offre sélectionnée'}, status=400)
            
            # Filtrer les offres selon les permissions de l'utilisateur
            if request.user.is_superuser:
                offres = Offre.objects.filter(id_offre__in=offre_ids)
            else:
                offres = Offre.objects.filter(
                    id_offre__in=offre_ids,
                    createur=request.user
                )
            
            # Vérifier que l'utilisateur a accès à toutes les offres
            if offres.count() != len(offre_ids) and not request.user.is_superuser:
                return JsonResponse({'error': 'Accès non autorisé à certaines offres'}, status=403)
            
            # Mapper les actions de l'interface vers les statuts Django
            if action == 'publish':
                offres.update(statut='publiee')
                message = f'{offres.count()} offre(s) publiée(s)'
            elif action == 'draft':
                offres.update(statut='brouillon')
                message = f'{offres.count()} offre(s) passée(s) en brouillon'
            elif action == 'delete':
                count = offres.count()
                offres.delete()
                message = f'{count} offre(s) supprimée(s)'
            else:
                return JsonResponse({'error': 'Action non valide'}, status=400)
            
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
# ==================== VUES DE TEST ====================


def form_test(request):
    """Test simple du formulaire"""
    from .forms import OffreForm
    form = OffreForm()
    
    return render(request, 'recrutement/form_test.html', {
        'form': form
    })


def liste_administrations(request):
    """
    Vue pour afficher la liste des administrations avec recherche.
    """
    # Récupérer le terme de recherche
    search_query = request.GET.get('q', '').strip()
    
    # Construire la requête de base
    administrations = Administration.objects.all().order_by('nom')
    
    # Appliquer la recherche si un terme est fourni
    if search_query:
        administrations = administrations.filter(
            Q(nom__icontains=search_query) |
            Q(ville__icontains=search_query) |
            Q(adresse__icontains=search_query) |
            Q(type_administration__icontains=search_query) 
        )
    
    # Compter le nombre de villes distinctes
    villes_count = Administration.objects.values('ville').distinct().count()
    
    # Filtrer par type si spécifié
    filter_type = request.GET.get('type', '')
    if filter_type:
        administrations = administrations.filter(type_administration=filter_type)
    
    # Filtrer par ville si spécifié
    filter_ville = request.GET.get('ville', '')
    if filter_ville:
        administrations = administrations.filter(ville__icontains=filter_ville)
    
    context = {
        'administrations': administrations,
        'villes_count': villes_count,
        'search_query': search_query,
        'filter_type': filter_type,
        'filter_ville': filter_ville,
    }
    
    return render(request, 'recrutement/administration.html', context)


def administration_detail_json(request, admin_id):
    """
    Vue API pour récupérer les détails d'une administration en JSON
    """
    try:
        admin = Administration.objects.get(id_administration=admin_id)
        
        data = {
            'id_administration': admin.id_administration,
            'nom': admin.nom,
            'type_administration': admin.type_administration,
            'adresse': admin.adresse,
            'ville': admin.ville,
            'description': admin.description if hasattr(admin, 'description') else '',
            # Ajoutez d'autres champs si nécessaire
        }
        
        return JsonResponse(data)
        
    except Administration.DoesNotExist:
        return JsonResponse({
            'error': 'Administration non trouvée'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


def administration_offres_json(request, admin_id):
    """
    Vue pour récupérer les offres d'une administration en JSON
    """
    administration = get_object_or_404(Administration, id_administration=admin_id)
    
    # Récupérer les offres actives de cette administration
    offres = Offre.objects.filter(
        administration=administration,
        est_active=True
    ).order_by('-date_publication')
    
    offres_data = []
    for offre in offres:
        offres_data.append({
            'id_offre': offre.id_offre,
            'titre': offre.titre,
            'description': offre.description,
            'type_contrat': offre.type_contrat,
            'date_publication': offre.date_publication.isoformat() if offre.date_publication else None,
            'date_limite': offre.date_limite.isoformat() if offre.date_limite else None,
            'est_active': offre.est_active,
            # Ajoutez d'autres champs si nécessaire
        })
    
    return JsonResponse(offres_data, safe=False)

# ==================== TABLEAU DE BORD RH ====================

@login_required
@rh_access_required
def rh_dashboard(request):
    """Tableau de bord RH"""
    # Compter les offres créées par cet utilisateur RH
    offres_rh = Offre.objects.filter(createur=request.user)
    candidatures = Candidature.objects.all()
    users = User.objects.all()
    # Statistiques
    total_users=users.count
    total_candidatures = candidatures.count()
    candidatures_deposees = candidatures.filter(statut='deposee').count()
    candidatures_en_revue = candidatures.filter(statut='en_revue').count()
    candidatures_retenues = candidatures.filter(statut='retenue').count()
    candidatures_rejetees = candidatures.filter(statut='rejetee').count()
    candidatures_embauche = candidatures.filter(statut='embauche').count()
    
    context = {
        'candidatures': candidatures,
        'total_candidatures': total_candidatures,
        'candidatures_deposees': candidatures_deposees,
        'candidatures_en_revue': candidatures_en_revue,
        'candidatures_retenues': candidatures_retenues,
        'candidatures_rejetees': candidatures_rejetees,
        'candidatures_embauche': candidatures_embauche,
    }
    # Compter les candidatures pour les offres de cet utilisateur RH
    candidatures_rh = Candidature.objects.filter(offre__createur=request.user)
    
    stats = {
        'total_offres_rh': offres_rh.count(),
        'total_users' : users.count,
        'offres_actives_rh': offres_rh.filter(statut='publiee').count(),
        'total_candidatures_rh': candidatures_rh.count(),
        'candidatures_recentes_rh': candidatures_rh.filter(
            date_depot__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }
    
    # Récupérer les candidatures récentes
    candidatures_recentes = candidatures_rh.select_related(
        'candidat', 'offre'
    ).order_by('-date_depot')[:10]
    
    # Récupérer les offres actives
    offres_actives = offres_rh.filter(
        statut='publiee',
        date_limite__gte=timezone.now().date()
    ).order_by('-date_publication')[:5]
    
    context = {
        'stats': stats,
        'candidatures_recentes': candidatures_recentes,
        'offres_actives': offres_actives,
        'active_page': 'rh_dashboard',
    }
    
    return render(request, 'recrutement/admin_dashboard.html', context)



@login_required
@user_passes_test(is_staff_user)
def gestion_candidatures(request):
    """Vue principale pour la gestion des candidatures par le RH"""
    
    # Filtrer les candidatures pour n'inclure que celles liées aux offres créées par le RH connecté
    candidatures = Candidature.objects.filter(
        offre__createur=request.user
    ).select_related('candidat', 'offre')
    
    # Appliquer les filtres
    filters = Q()
    
    # Filtre par statut
    statut = request.GET.get('statut')
    if statut:
        filters &= Q(statut=statut)
    
    # Filtre par offre (seulement les offres du RH)
    offre_id = request.GET.get('offre')
    if offre_id:
        filters &= Q(offre_id=offre_id)
    
    # Filtre par date
    date_debut = request.GET.get('date_debut')
    if date_debut:
        filters &= Q(date_depot__date__gte=date_debut)
    
    date_fin = request.GET.get('date_fin')
    if date_fin:
        filters &= Q(date_depot__date__lte=date_fin)
    
    # Filtre par recherche texte
    recherche = request.GET.get('recherche')
    if recherche:
        filters &= (
            Q(candidat__first_name__icontains=recherche) |
            Q(candidat__last_name__icontains=recherche) |
            Q(candidat__email__icontains=recherche) |
            Q(offre__titre__icontains=recherche) |
            Q(offre__departement__icontains=recherche)
        )
    
    # Appliquer les filtres
    candidatures = candidatures.filter(filters)
    
    # Appliquer le tri
    tri = request.GET.get('tri', '-date_depot')
    candidatures = candidatures.order_by(tri)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(candidatures, 20)  # 20 candidatures par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculer les statistiques SEULEMENT pour les offres du RH
    total_candidatures = candidatures.count()  # Utiliser le queryset filtré
    
    context = {
        'page_obj': page_obj,
        'candidatures': page_obj.object_list,
        'total_candidatures': total_candidatures,
        'candidatures_deposees': candidatures.filter(statut='deposee').count(),
        'candidatures_en_revue': candidatures.filter(statut='en_revue').count(),
        'candidatures_retenues': candidatures.filter(statut='retenue').count(),
        'candidatures_rejetees': candidatures.filter(statut='rejetee').count(),
        'candidatures_convoque': candidatures.filter(statut='convoque').count(),
        'candidatures_embauche': candidatures.filter(statut='embauche').count(),
        'statut_choices': Candidature.STATUT_CHOICES,
        'offres': Offre.objects.filter(createur=request.user),
    }
    
    return render(request, 'recrutement/gestion_candidatures.html', context)

@login_required
@rh_access_required
def changer_statut_candidature(request, candidature_id):
    """Vue pour changer le statut d'une candidature"""
    # Utilisez 'id_candidature' au lieu de 'id'
    candidature = get_object_or_404(Candidature, id_candidature=candidature_id)
    
    # Vérifier si la candidature appartient à une offre créée par le RH
    if candidature.offre.createur != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cette candidature.")
        return redirect('gestion_candidatures')
    
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        date_validation = request.POST.get('date_validation')
        
        candidature.statut = nouveau_statut
        
        if date_validation:
            candidature.date_validation = date_validation
        
        if nouveau_statut == 'retenue':
            candidature.valide = True
        
        candidature.save()
        
        # Ajouter un log d'activité
        messages.success(request, f'Statut de la candidature mis à jour: {candidature.get_statut_display()}')
        
        # Rediriger vers la page précédente
        referer = request.META.get('HTTP_REFERER', '/rh/candidatures/')
        return redirect(referer)
    
    return redirect('gestion_candidatures')

@login_required
@rh_access_required
def ajouter_commentaire_rh(request, candidature_id):
    """Vue pour ajouter/modifier un commentaire RH"""
    candidature = get_object_or_404(Candidature, id_candidature=candidature_id)
    
    # Vérifier si la candidature appartient à une offre créée par le RH
    if candidature.offre.createur != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cette candidature.")
        return redirect('gestion_candidatures')
    
    if request.method == 'POST':
        commentaire = request.POST.get('commentaire_rh', '').strip()
        
        candidature.commentaire_rh = commentaire
        candidature.save()
        
        messages.success(request, 'Commentaire RH enregistré avec succès')
        
        # Retour à la page précédente ou à la gestion des candidatures
        referer = request.META.get('HTTP_REFERER', '/rh/candidatures/')
        return redirect(referer)
    
    # Pour GET, retourner directement à la page de gestion
    return redirect('gestion_candidatures')

@login_required
@rh_access_required
def supprimer_candidature(request, candidature_id):
    """Vue pour supprimer une candidature"""
    # Utilisez 'id_candidature' au lieu de 'id'
    candidature = get_object_or_404(Candidature, id_candidature=candidature_id)
    
    if request.method == 'POST':
        candidat_nom = f"{candidature.candidat.get_full_name()}"
        offre_titre = candidature.offre.titre
        
        # Supprimer les fichiers associés si nécessaire
        if candidature.cv:
            candidature.cv.delete(save=False)
        if candidature.lettre_motivation:
            candidature.lettre_motivation.delete(save=False)
        
        # Supprimer la candidature
        candidature.delete()
        
        messages.success(request, f'Candidature de {candidat_nom} pour "{offre_titre}" supprimée avec succès')
        return redirect('gestion_candidatures')
    
    return redirect('gestion_candidatures')

@login_required
@rh_access_required
def detail_candidature(request, candidature_id):
    """Vue pour voir les détails d'une candidature"""
    # Utilisez 'id_candidature' au lieu de 'id'
    candidature = get_object_or_404(Candidature, id_candidature=candidature_id)
    
    # Vérifier si la candidature appartient à une offre créée par le RH
    if candidature.offre.createur != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir cette candidature.")
        return redirect('gestion_candidatures')
    
    context = {
        'candidature': candidature,
    }
    
    return render(request, 'recrutement/detail_candidature.html', context)

@login_required
@rh_access_required
def export_candidatures(request):
    """Vue pour exporter les candidatures en CSV"""
    # Créer la réponse HTTP avec l'en-tête CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="candidatures_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # En-têtes du CSV
    writer.writerow([
        'ID', 'Candidat', 'Email', 'Offre', 'Département',
        'Date dépôt', 'Statut', 'Validé', 'CV', 'Lettre motivation',
        'Commentaire RH', 'Commentaire candidat'
    ])
    
    # Récupérer les candidatures des offres créées par le RH connecté
    candidatures = Candidature.objects.filter(
        offre__createur=request.user
    ).select_related('candidat', 'offre')
    
    # Appliquer les mêmes filtres que dans la vue principale
    statut = request.GET.get('statut')
    if statut:
        candidatures = candidatures.filter(statut=statut)
    
    offre_id = request.GET.get('offre')
    if offre_id:
        candidatures = candidatures.filter(offre_id=offre_id)
    
    date_debut = request.GET.get('date_debut')
    if date_debut:
        candidatures = candidatures.filter(date_depot__date__gte=date_debut)
    
    date_fin = request.GET.get('date_fin')
    if date_fin:
        candidatures = candidatures.filter(date_depot__date__lte=date_fin)
    
    # Écrire les données
    for c in candidatures:
        writer.writerow([
            c.id_candidature,
            c.candidat.get_full_name(),
            c.candidat.email,
            c.offre.titre,
            c.offre.departement,
            c.date_depot.strftime('%Y-%m-%d %H:%M:%S'),
            c.get_statut_display(),
            'Oui' if c.valide else 'Non',
            'Oui' if c.cv else 'Non',
            'Oui' if c.lettre_motivation else 'Non',
            c.commentaire_rh[:100] + '...' if len(c.commentaire_rh) > 100 else c.commentaire_rh,
            c.commentaire_candidat[:100] + '...' if len(c.commentaire_candidat) > 100 else c.commentaire_candidat,
        ])
    
    return response




# ==================== GESTION DES UTILISATEURS ====================

@login_required
@user_passes_test(is_staff_user)
def gestion_utilisateurs(request):
    """Interface de gestion des utilisateurs"""
    
    
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    filters = Q()
    
    role = request.GET.get('role')
    if role:
        filters &= Q(profile__role=role)
    
    is_active = request.GET.get('is_active')
    if is_active == 'actif':
        filters &= Q(is_active=True)
    elif is_active == 'inactif':
        filters &= Q(is_active=False)
    
    search = request.GET.get('search')
    if search:
        filters &= (
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(profile__phone__icontains=search) |
            Q(profile__profession__icontains=search)
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        filters &= Q(date_joined__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        filters &= Q(date_joined__date__lte=date_to)
    
    users = users.filter(filters)
    
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    role_counts = {}
    for role_code, role_name in UserProfile.ROLE_CHOICES:
        role_counts[role_code] = {
            'name': role_name,
            'count': User.objects.filter(profile__role=role_code).count()
        }
    
    context = {
        'page_obj': page_obj,
        'users': page_obj.object_list,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'superusers': User.objects.filter(is_superuser=True).count(),
        'role_counts': role_counts,
        'role_choices': UserProfile.ROLE_CHOICES,
        'selected_role_choices': UserProfile.SELECTED_ROLE_CHOICES,
        'niveau_etude_choices': [
            ('bac', 'Baccalauréat'),
            ('bac+2', 'Bac+2'),
            ('bac+3', 'Licence'),
            ('bac+5', 'Master'),
            ('doctorat', 'Doctorat'),
            ('autre', 'Autre'),
        ]
    }
    
    return render(request, 'recrutement/gestion_utilisateurs.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def detail_utilisateur(request, user_id):
    """Détail d'un utilisateur"""
    user_detail = get_object_or_404(User, pk=user_id)
    
    # S'assurer que le profil existe
    if not hasattr(user_detail, 'profile'):
        UserProfile.objects.create(user=user_detail)
        user_detail.refresh_from_db()
    
    # Récupérer les candidatures de l'utilisateur
    candidatures = Candidature.objects.filter(candidat=user_detail).select_related('offre')
    
    # Statistiques des candidatures
    stats_candidatures = {
        'total': candidatures.count(),
        'deposees': candidatures.filter(statut='deposee').count(),
        'en_revue': candidatures.filter(statut='en_revue').count(),
        'retenues': candidatures.filter(statut='retenue').count(),
        'rejetees': candidatures.filter(statut='rejetee').count(),
        'convoques': candidatures.filter(statut='convoque').count(),
        'embauches': candidatures.filter(statut='embauche').count(),
    }
    
    # Activité récente
    last_activity = "Jamais connecté"
    if user_detail.last_login:
        delta = timezone.now() - user_detail.last_login
        total_seconds = int(delta.total_seconds())
        if total_seconds > 86400:  # plus d'un jour
            days = total_seconds // 86400
            last_activity = f"Il y a {days} jour{'s' if days > 1 else ''}"
        elif total_seconds > 3600:
            hours = total_seconds // 3600
            last_activity = f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif total_seconds > 60:
            minutes = total_seconds // 60
            last_activity = f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            last_activity = "À l'instant"
    
    context = {
        'user_detail': user_detail,  # Nom dans le template
        'profile': user_detail.profile,
        'candidatures': candidatures.order_by('-date_depot')[:10],
        'stats_candidatures': stats_candidatures,
        'last_login': user_detail.last_login,
        'last_activity': last_activity,
        'inscription_ago': timezone.now() - user_detail.date_joined,
        'jours_inscription': (timezone.now() - user_detail.date_joined).days,
        'current_user': request.user  # Pour référence dans le template
    }
    
    return render(request, 'recrutement/detail_utilisateur.html', context)
@login_required
@user_passes_test(is_staff_user)
def modifier_utilisateur(request, user_id):
    """Modifier un utilisateur"""
    user = get_object_or_404(user, pk=user_id)
    
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        try:
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.is_active = 'is_active' in request.POST
            
            if request.user.is_superuser:
                user.is_staff = 'is_staff' in request.POST
                user.is_superuser = 'is_superuser' in request.POST
            
            user.save()
            
            profile = user.profile
            profile.phone = request.POST.get('phone', profile.phone)
            profile.address = request.POST.get('address', profile.address)
            profile.postal_code = request.POST.get('postal_code', profile.postal_code)
            profile.city = request.POST.get('city', profile.city)
            profile.country = request.POST.get('country', profile.country)
            profile.profession = request.POST.get('profession', profile.profession)
            profile.niveau_etude = request.POST.get('niveau_etude', profile.niveau_etude)
            
            experience = request.POST.get('experience')
            if experience is not None:
                try:
                    profile.experience = int(experience)
                except ValueError:
                    profile.experience = 0
            
            profile.role = request.POST.get('role', profile.role)
            profile.selected_role = request.POST.get('selected_role', profile.selected_role)
            
            profile.save()
            
            messages.success(request, f"L'utilisateur {user.username} a été mis à jour avec succès.")
            return redirect('detail_utilisateur', user_id=user_id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
    
    context = {
        'user_edit': user,
        'profile': user.profile,
        'role_choices': UserProfile.ROLE_CHOICES,
        'selected_role_choices': UserProfile.SELECTED_ROLE_CHOICES,
        'niveau_etude_choices': [
            ('bac', 'Baccalauréat'),
            ('bac+2', 'Bac+2'),
            ('bac+3', 'Licence'),
            ('bac+5', 'Master'),
            ('doctorat', 'Doctorat'),
            ('autre', 'Autre'),
        ]
    }
    
    return render(request, 'recrutement/modifier_utilisateur.html', context)

@login_required
@user_passes_test(is_staff_user)
def creer_utilisateur_manuel(request):
    """Créer un utilisateur manuellement"""
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            role = request.POST.get('role', 'candidat')
            
            if not all([username, email, password]):
                messages.error(request, "Username, email et mot de passe sont obligatoires.")
                return redirect('gestion_utilisateurs')
            
            if user.objects.filter(username=username).exists():
                messages.error(request, "Ce nom d'utilisateur existe déjà.")
                return redirect('gestion_utilisateurs')
            
            if user.objects.filter(email=email).exists():
                messages.error(request, "Cet email existe déjà.")
                return redirect('gestion_utilisateurs')
            
            user = user.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            if role == 'rh':
                user.is_staff = True
                user.save()
            elif role == 'admin' or role == 'superadmin':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            profile = user.profile
            profile.role = role
            profile.selected_role = 'user' if role == 'candidat' else role
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.profession = request.POST.get('profession', '')
            profile.save()
            
            messages.success(request, f"Utilisateur {username} créé avec succès.")
            return redirect('detail_utilisateur', user_id=user.id)
            
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
    
    return redirect('gestion_utilisateurs')

@login_required
@user_passes_test(is_staff_user)
def exporter_utilisateurs_csv(request):
    """Exporter les utilisateurs en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="utilisateurs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response, delimiter=';')
    
    writer.writerow([
        'ID', 'Username', 'Email', 'Prénom', 'Nom', 'Rôle', 'Statut',
        'Téléphone', 'Profession', 'Expérience', 'Niveau étude',
        'Date inscription', 'Dernière connexion', 'Staff', 'Superuser'
    ])
    
    users = user.objects.all().select_related('profile')
    
    role = request.GET.get('role')
    if role:
        users = users.filter(profile__role=role)
    
    is_active = request.GET.get('is_active')
    if is_active == 'actif':
        users = users.filter(is_active=True)
    elif is_active == 'inactif':
        users = users.filter(is_active=False)
    
    for user in users:
        profile = user.profile
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            profile.get_role_display(),
            'Actif' if user.is_active else 'Inactif',
            profile.phone,
            profile.profession,
            profile.experience,
            profile.get_niveau_etude_display() if profile.niveau_etude else '',
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            'Oui' if user.is_staff else 'Non',
            'Oui' if user.is_superuser else 'Non'
        ])
    
    return response

@login_required
@user_passes_test(is_staff_user)
def supprimer_utilisateur(request, user_id):
    """Supprimer un utilisateur"""
    # CORRECTION : Utiliser 'User' (majuscule) pour le modèle Django
    utilisateur_cible = get_object_or_404(User, pk=user_id)
    
    # Empêcher la suppression de soi-même
    if utilisateur_cible == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('detail_utilisateur', user_id=user_id)
    
    if request.method == 'POST':
        username = utilisateur_cible.username
        
        try:
            # Supprimer les fichiers uploadés du profil si existent
            if hasattr(utilisateur_cible, 'profile'):
                profile = utilisateur_cible.profile
                if profile.cv_default:
                    profile.cv_default.delete(save=False)
                if profile.cover_letter:
                    profile.cover_letter.delete(save=False)
        except UserProfile.DoesNotExist:
            pass  # Pas de profil, on continue
        except AttributeError:
            pass  # Pas d'attribut, on continue
        
        # Supprimer l'utilisateur
        utilisateur_cible.delete()
        
        messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
        return redirect('gestion_utilisateurs')
    
    # Si méthode GET, afficher la confirmation
    context = {'user': utilisateur_cible}  # Ici 'user' est correct pour le template
    return render(request, 'recrutement/confirmation_suppression_utilisateur.html', context)
@login_required
@user_passes_test(is_staff_user)
def changer_statut_utilisateur(request, user_id):
    """Changer le statut d'activation d'un utilisateur"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'activate':
            user.is_active = True
            message = f"L'utilisateur {user.username} a été activé."
        elif action == 'deactivate':
            user.is_active = False
            message = f"L'utilisateur {user.username} a été désactivé."
        else:
            messages.error(request, "Action non valide.")
            return redirect('detail_utilisateur', user_id=user_id)
        
        user.save()
        messages.success(request, message)
    
    return redirect('detail_utilisateur', user_id=user_id)


# ==================== NOTIFICATIONS ====================

@login_required
def notifications_view(request):
    """Page de notifications"""
    # Filtrage par type
    notification_type = request.GET.get('type')
    notifications = Notification.objects.filter(user=request.user)
    
    if notification_type:
        notifications = notifications.filter(type_notification=notification_type)
    
    notifications = notifications.order_by('-date_creation')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_count = notifications.count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    read_count = total_count - unread_count  # <-- CALCUL ICI
    
    context = {
        'notifications': page_obj,
        'unread_count': unread_count,
        'read_count': read_count,  # <-- AJOUTEZ CECI
        'total_count': total_count,  # <-- AJOUTEZ CECI
        'active_page': 'notifications',
    }
    
    return render(request, 'recrutement/notifications/list.html', context)

@login_required
def get_unread_notifications(request):
    """API pour récupérer les notifications non lues (pour AJAX)"""
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-date_creation')[:10]
    
    data = []
    for notification in notifications:
        data.append({
            'id': notification.id_notification,
            'titre': notification.titre,
            'message': notification.message,
            'type': notification.type_notification,
            'url': notification.url,
            'time_since': notification.time_since(),
            'is_read': notification.is_read,
        })
    
    return JsonResponse({
        'notifications': data,
        'count': notifications.count(),
        'total_unread': Notification.objects.filter(user=request.user, is_read=False).count()
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Marquer une notification comme lue"""
    try:
        notification = Notification.objects.get(
            id_notification=notification_id, 
            user=request.user
        )
        notification.is_read = True
        notification.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, "Notification marquée comme lue.")
        
    except Notification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Notification non trouvée'}, status=404)
        messages.error(request, "Notification non trouvée.")
    
    return redirect('notifications_view')

@login_required
@require_POST
def mark_all_notifications_read(request):
    """Marquer toutes les notifications comme lues"""
    try:
        updated_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'updated_count': updated_count
            })
        
        messages.success(request, f"{updated_count} notification(s) marquée(s) comme lue(s).")
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        messages.error(request, f"Erreur: {str(e)}")
    
    return redirect('notifications_view')

@login_required
@require_POST
def delete_notification(request, notification_id):
    """Supprimer une notification"""
    try:
        notification = Notification.objects.get(
            id_notification=notification_id, 
            user=request.user
        )
        notification.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, "Notification supprimée.")
        
    except Notification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Notification non trouvée'}, status=404)
        messages.error(request, "Notification non trouvée.")
    
    return redirect('notifications_view')

@login_required
@require_POST
def clear_all_notifications(request):
    """Supprimer toutes les notifications"""
    try:
        deleted_count, _ = Notification.objects.filter(user=request.user).delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'deleted_count': deleted_count
            })
        
        messages.success(request, f"{deleted_count} notification(s) supprimée(s).")
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        messages.error(request, f"Erreur: {str(e)}")
    
    return redirect('notifications_view')

@login_required
def notification_badge(request):
    """Retourne le nombre de notifications non lues pour le badge"""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

# ==================== UTILITAIRES NOTIFICATIONS ====================

def create_notification(user, titre, message, type_notification='info', url=None):
    """
    Créer une nouvelle notification pour un utilisateur
    
    Args:
        user: L'utilisateur destinataire
        titre: Titre de la notification
        message: Message de la notification
        type_notification: Type (info, success, warning, error, system)
        url: URL de redirection optionnelle
    """
    try:
        notification = Notification.objects.create(
            user=user,
            titre=titre,
            message=message,
            type_notification=type_notification,
            url=url,
            date_creation=timezone.now(),
            is_read=False
        )
        return notification
    except Exception as e:
        print(f"Erreur lors de la création de la notification: {e}")
        return None

def create_notification_for_staff(titre, message, type_notification='info', url=None):
    """
    Créer une notification pour tous les utilisateurs staff
    
    Args:
        titre: Titre de la notification
        message: Message de la notification
        type_notification: Type (info, success, warning, error, system)
        url: URL de redirection optionnelle
    """
    staff_users = User.objects.filter(is_staff=True)
    notifications = []
    
    for user in staff_users:
        notification = create_notification(
            user=user,
            titre=titre,
            message=message,
            type_notification=type_notification,
            url=url
        )
        if notification:
            notifications.append(notification)
    
    return notifications

def create_notification_for_all_users(titre, message, type_notification='info', url=None):
    """
    Créer une notification pour tous les utilisateurs
    
    Args:
        titre: Titre de la notification
        message: Message de la notification
        type_notification: Type (info, success, warning, error, system)
        url: URL de redirection optionnelle
    """
    all_users = User.objects.filter(is_active=True)
    notifications = []
    
    for user in all_users:
        notification = create_notification(
            user=user,
            titre=titre,
            message=message,
            type_notification=type_notification,
            url=url
        )
        if notification:
            notifications.append(notification)
    
    return notifications

def create_bulk_notifications(users, titre, message, type_notification='info', url=None):
    """
    Créer des notifications pour une liste d'utilisateurs
    
    Args:
        users: Liste ou QuerySet d'utilisateurs
        titre: Titre de la notification
        message: Message de la notification
        type_notification: Type (info, success, warning, error, system)
        url: URL de redirection optionnelle
    """
    notifications = []
    
    for user in users:
        notification = create_notification(
            user=user,
            titre=titre,
            message=message,
            type_notification=type_notification,
            url=url
        )
        if notification:
            notifications.append(notification)
    
    return notifications


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def update_user_permissions(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Mettre à jour le rôle
        role = request.POST.get('role')
        if role in ['candidat', 'rh', 'admin']:
            profile.role = role
            profile.save()
        
        # Mettre à jour les permissions Django
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        user.save()
        
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def forgot_password_check(request):
    """Vérification ID + Email avant réinitialisation"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(username=username, email=email)
            
            # Stocker l'ID de l'utilisateur en session sécurisée
            request.session['reset_user_id'] = user.id
            request.session['reset_verified'] = True
            
            messages.success(request, "Vérification réussie ! Vous pouvez maintenant réinitialiser votre mot de passe.")
            return redirect('reset_password_new')
            
        except User.DoesNotExist:
            messages.error(request, "L'ID et l'email ne correspondent pas ou l'utilisateur n'existe pas.")
    
    return render(request, 'recrutement/forgot_password_check.html')

@csrf_protect
def reset_password_new_simple(request):
    """Réinitialisation du mot de passe après vérification"""
    # Vérifier si l'utilisateur a passé la vérification
    if not request.session.get('reset_verified'):
        messages.error(request, "Veuillez d'abord vérifier vos informations.")
        return redirect('forgot_password_check')
    
    user_id = request.session.get('reset_user_id')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Session invalide. Veuillez recommencer.")
        return redirect('forgot_password_check')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation simple
        if not new_password or not confirm_password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, 'recrutement/reset_password_new_simple.html', {'user': user})
        
        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'recrutement/reset_password_new_simple.html', {'user': user})
        
        if len(new_password) < 6:
            messages.error(request, "Le mot de passe doit contenir au moins 6 caractères.")
            return render(request, 'recrutement/reset_password_new_simple.html', {'user': user})
        
        # Mettre à jour le mot de passe
        user.set_password(new_password)
        user.save()
        
        # Nettoyer la session
        request.session.pop('reset_user_id', None)
        request.session.pop('reset_verified', None)
        
        # Déconnecter toutes les sessions existantes
        logout(request)
        
        messages.success(request, f"Mot de passe réinitialisé avec succès pour l'utilisateur {user.username} !")
        return redirect('login')
    
    return render(request, 'recrutement/reset_password_new_simple.html', {'user': user})



    # ==================== gestion des administration ====================
@login_required
@user_passes_test(is_superadmin)
def gestion_administrations(request):
    administrations = Administration.objects.all().order_by('nom')
    return render(request, 'recrutement/administration/gestion_administrations.html', {
        'administrations': administrations,
        'total_count': administrations.count(),
        'ministere_count': administrations.filter(type_administration='ministere').count(),
        'collectivite_count': administrations.filter(type_administration='collectivite').count(),
    })

@login_required
@user_passes_test(is_superadmin)
def creer_administration(request):
    if request.method == 'POST':
        form = AdministrationForm(request.POST)
        if form.is_valid():
            admin = form.save()
            messages.success(request, f" L'administration '{admin.nom}' a été créée avec succès.")
            return redirect('gestion_administrations')
    else:
        form = AdministrationForm()
    
    return render(request, 'recrutement/administration/creer_administration.html', {
        'form': form,
        'action': 'Créer',
    })

@login_required
@user_passes_test(is_superadmin)
def modifier_administration(request, id):
    administration = get_object_or_404(Administration, id_administration=id)
    
    if request.method == 'POST':
        form = AdministrationForm(request.POST, instance=administration)
        if form.is_valid():
            admin = form.save()
            messages.success(request, f" L'administration '{admin.nom}' a été mise à jour.")
            return redirect('gestion_administrations')
    else:
        form = AdministrationForm(instance=administration)
    
    return render(request, 'recrutement/administration/modifier_administration.html', {
        'form': form,
        'administration': administration,
        'action': 'Modifier',
    })

@login_required
@user_passes_test(is_superadmin)
def supprimer_administration(request, id):
    administration = get_object_or_404(Administration, id_administration=id)
    
    if request.method == 'POST':
        nom = administration.nom
        administration.delete()
        messages.success(request, f"L'administration '{nom}' a été supprimée.")
        return redirect('gestion_administrations')
    
    return render(request, 'recrutement/administration/supprimer_administration.html', {
        'administration': administration,
    })