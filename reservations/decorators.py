from functools import wraps
from django.shortcuts import redirect


def login_required_custom(view_func):
    """
    Décorateur personnalisé pour vérifier que l'utilisateur est connecté.
    Vérifie la présence de 'user_id' dans la session.
    Redirige vers la page de login si l'utilisateur n'est pas connecté.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            # Rediriger vers la page de login avec le paramètre next
            return redirect(f'/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

