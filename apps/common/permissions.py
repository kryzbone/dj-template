from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()


def check_auth(request):
    return request.user.is_authenticated


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return check_auth(request) and user.role == User.Roles.USER

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user if check_auth(request) else False
