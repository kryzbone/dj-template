"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# API Docs setup
schema_view = get_schema_view(
    openapi.Info(
        title="API Project",
        default_version="v1",
        description="API Project description",
        terms_of_service="",
        contact=openapi.Contact(email="example@email.com", name="kryzbone"),
        license=openapi.License(name="Copyright"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


# Authentication views for redoc and swagger
# To Use: Replace corresponding view with these login_required views
# Use django.contrib.auth.views.decorators.login_required() to add login to a view
# U can also use django.contrib.admin.views.decorators.staff_member_required()
# -------------------------------------------------------------------------------------
# Redoc Schema
@staff_member_required(login_url="/login/")
def redoc(request):
    return schema_view.with_ui("redoc", cache_timeout=0)(request)


# Swagger Schema
@staff_member_required(login_url="/login/")
def swagger(request):
    return schema_view.with_ui("swagger", cache_timeout=0)(request)


urlpatterns = [
    # Home and Login pages
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    # Open API Docs
    # -------------------------------------------------------------------------------
    # path("docs/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # path(
    #   "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui",
    # ),
    # Protected API Docs
    # -----------------------------------------------------------------------------------
    path("docs/", redoc, name="schema-redoc"),
    path("swagger-docs/", swagger, name="schema-swagger-ui"),
    path("admin/", admin.site.urls),
]

# API URLS
urlpatterns += [
    # API URLs
    path("api/", include("config.api_urls")),
]

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns = [path("__debug__/", include("debug_toolbar.urls"))] + urlpatterns
