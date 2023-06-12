from django.urls.conf import include, path

app_name = "api"

urlpatterns = [
    path("", include("apps.users.urls")),
]
