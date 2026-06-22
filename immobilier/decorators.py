from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def superuser_required(view_func):
    """Decorator to require superuser access."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Vous devez être administrateur pour accéder à cette page.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_superuser_required(view_func):
    """Decorator to require staff or superuser access."""
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Accès non autorisé.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
