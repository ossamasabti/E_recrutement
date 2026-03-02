# recrutement/context_processors.py

def user_context(request):
    if request.user.is_authenticated:
        est_admin_rh = (
            request.user.is_staff or
            hasattr(request.user, 'administrateurrh') or
            request.user.groups.filter(name='Admin_RH').exists()
        )
    else:
        est_admin_rh = False

    return {
        'est_admin_rh': est_admin_rh
    }