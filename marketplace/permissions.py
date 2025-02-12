from rest_framework import permissions

class IsAdminOrSeller(permissions.BasePermission):
    """
    Custom permission:
    - Admin: Can perform any action.
    - Seller: Can perform CRUD on their own products only.
    - Basic Users: Read-only access.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False  

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:  
            return True
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return obj.product_provider == request.user  
