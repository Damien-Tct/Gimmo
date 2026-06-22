from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée : admin en écriture, tout le monde en lecture.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsProprietaireOrStaff(permissions.BasePermission):
    """
    Permet l'accès si l'utilisateur est staff ou propriétaire du bien.
    """
    def has_object_permission(self, request, view, obj):
        # Staff peut tout voir
        if request.user.is_staff:
            return True
        # Vérification si l'objet a un champ proprietaire
        if hasattr(obj, 'proprietaire'):
            return obj.proprietaire.email == request.user.email
        if hasattr(obj, 'bien') and hasattr(obj.bien, 'proprietaire'):
            return obj.bien.proprietaire.email == request.user.email
        if hasattr(obj, 'locataire'):
            return obj.locataire.email == request.user.email
        return False
