# Skill: Scaffold a New Django App

Use this skill when adding a completely new feature/resource to the project (e.g., "add a blog feature", "add products", "add orders").

---

## Prerequisites

- Know the app name (e.g., `blog`, `products`, `orders`)
- Know the primary model fields for this resource
- Django project is running (migrations work, tests pass)

---

## Step 1 — Create the App Directory

```bash
python manage.py startapp <appname> apps/<appname>
```

This creates: `apps/<appname>/` with `models.py`, `views.py`, `admin.py`, `apps.py`, `migrations/`, etc.

---

## Step 2 — Fix `apps.py`

Open `apps/<appname>/apps.py`. Set the correct `name`:

```python
from django.apps import AppConfig


class <AppnameConfig>(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.<appname>"  # MUST include "apps." prefix
```

---

## Step 3 — Register in Settings

In `config/settings/base.py`, add to `LOCAL_APPS`:

```python
LOCAL_APPS = [
    "apps.users.apps.UsersConfig",
    "apps.common",
    "apps.<appname>.apps.<AppnameConfig>",  # Add this line
]
```

---

## Step 4 — Create the Model

In `apps/<appname>/models.py`:

```python
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class <ModelName>(BaseModel):
    """
    Brief description of the model.
    """

    # Example fields — replace with your actual fields:
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    # For foreign keys:
    # owner = models.ForeignKey(
    #     "users.User",
    #     on_delete=models.CASCADE,
    #     related_name="<appname>s",
    # )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("<model name>")
        verbose_name_plural = _("<model names>")

    def __str__(self) -> str:
        return self.name
```

**Rules:**
- Always inherit from `BaseModel` — never `models.Model`
- Always define `ordering` in Meta
- Always define `__str__`
- Use `gettext_lazy` for all user-visible strings
- UUID primary key is inherited from `BaseModel` — do not define `id`

---

## Step 5 — Run Migrations

```bash
python manage.py makemigrations <appname>
python manage.py migrate
```

---

## Step 6 — Create Serializers

Create `apps/<appname>/serializers.py`:

```python
from rest_framework import serializers

from .<models> import <ModelName>


class <ModelName>Serializer(serializers.ModelSerializer):
    class Meta:
        model = <ModelName>
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class <ModelName>WriteSerializer(serializers.ModelSerializer):
    """Used for create/update operations when input fields differ from output."""

    class Meta:
        model = <ModelName>
        fields = ["name", "description"]

    def validate_name(self, value: str) -> str:
        # Example single-field validation
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        return value
```

**Rules:**
- Read serializers: include `id`, `created_at`, `updated_at` as `read_only_fields`
- Write serializers: only include writable fields
- `password` fields always use `write_only=True`
- Use `validate_<field>()` for field-level validation
- Use `validate()` for cross-field validation

---

## Step 7 — Create Views

Create `apps/<appname>/views.py`:

```python
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .<models> import <ModelName>
from .serializers import <ModelName>Serializer, <ModelName>WriteSerializer


class <ModelName>View(
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    """
    ViewSet for <ModelName> CRUD operations.
    """

    queryset = <ModelName>.objects.filter(is_active=True)
    serializer_class = <ModelName>Serializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_active"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "updated_at", "name"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return <ModelName>WriteSerializer
        return <ModelName>Serializer

    def get_queryset(self):
        # Scope to authenticated user's data if needed:
        # return self.queryset.filter(owner=self.request.user)
        return self.queryset

    @swagger_auto_schema(method="GET", responses={200: <ModelName>Serializer(many=True)})
    @action(detail=False, methods=["GET"])
    def active(self, request):
        """List only active records."""
        qs = self.get_queryset().filter(is_active=True)
        serializer = <ModelName>Serializer(qs, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)
```

**Rules:**
- Always set `permission_classes` explicitly
- Use `get_serializer_class()` to serve different serializers for read vs write
- Use `get_queryset()` to scope data to the current user
- Document custom `@action` endpoints with `@swagger_auto_schema`
- Include only the mixins you actually need

---

## Step 8 — Create URLs

Create `apps/<appname>/urls.py`:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import <ModelName>View

router = DefaultRouter()
router.register("<appname>", <ModelName>View, basename="<appname>")

urlpatterns = [
    path("", include(router.urls)),
]
```

---

## Step 9 — Register URLs in `config/api_urls.py`

```python
from django.urls.conf import include, path

app_name = "api"

urlpatterns = [
    path("", include("apps.users.urls")),
    path("", include("apps.<appname>.urls")),  # Add this line
]
```

URL names are automatically generated by the router:
- `api:<appname>-list` → `GET /api/<appname>/`
- `api:<appname>-detail` → `GET/PATCH/DELETE /api/<appname>/<id>/`
- `api:<appname>-active` → `GET /api/<appname>/active/`

---

## Step 10 — Register in Admin

In `apps/<appname>/admin.py`:

```python
from django.contrib import admin

from .<models> import <ModelName>


@admin.register(<ModelName>)
class <ModelName>Admin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
```

---

## Step 11 — Create Tests

Create the test directory structure:

```
apps/<appname>/tests/
    __init__.py
    factories.py
    test_models.py
    test_views.py
```

**`apps/<appname>/tests/factories.py`:**

```python
from factory import Faker
from factory.django import DjangoModelFactory

from apps.<appname>.models import <ModelName>


class <ModelName>Factory(DjangoModelFactory):
    name = Faker("sentence", nb_words=3)
    description = Faker("paragraph")

    class Meta:
        model = <ModelName>
```

**`apps/<appname>/tests/test_views.py`:**

```python
import pytest
from django.urls import reverse
from rest_framework import status

from apps.<appname>.models import <ModelName>
from apps.<appname>.tests.factories import <ModelName>Factory

pytestmark = pytest.mark.django_db


class Test<ModelName>View:
    def test_list(self, api_client_auth, user):
        <ModelName>Factory.create_batch(3)
        url = reverse("api:<appname>-list")
        client = api_client_auth(user)

        resp = client.get(url)
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert "results" in data

    def test_create(self, api_client_auth, user):
        url = reverse("api:<appname>-list")
        client = api_client_auth(user)
        payload = {"name": "Test Item", "description": "A description"}

        resp = client.post(url, data=payload)
        data = resp.json()

        assert resp.status_code == status.HTTP_201_CREATED
        assert data["name"] == payload["name"]

    def test_retrieve(self, api_client_auth, user):
        obj = <ModelName>Factory()
        url = reverse("api:<appname>-detail", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.get(url)
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert data["id"] == str(obj.id)

    def test_update(self, api_client_auth, user):
        obj = <ModelName>Factory()
        url = reverse("api:<appname>-detail", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.patch(url, data={"name": "Updated Name"})
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert data["name"] == "Updated Name"

    def test_delete(self, api_client_auth, user):
        obj = <ModelName>Factory()
        url = reverse("api:<appname>-detail", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.delete(url)

        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_access_denied(self, api_client):
        url = reverse("api:<appname>-list")

        resp = api_client.get(url)

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
```

---

## Checklist

Before marking the feature complete:

- [ ] App is in `apps/` directory
- [ ] `apps.py` has correct `name = "apps.<appname>"`
- [ ] App registered in `LOCAL_APPS` in `config/settings/base.py`
- [ ] Model inherits from `BaseModel`
- [ ] `__str__` defined on model
- [ ] `ordering` defined in model Meta
- [ ] Migrations created and applied
- [ ] Serializers created (read and write if needed)
- [ ] View has explicit `permission_classes`
- [ ] URLs registered in `config/api_urls.py`
- [ ] Admin registered
- [ ] Factory created in `tests/factories.py`
- [ ] Tests cover: list, create, retrieve, update, delete, unauthenticated access
- [ ] All tests pass: `pytest apps/<appname>/`
