# Django Template — AI Agent Instructions

This is a Django 5.1 REST API template using Django REST Framework. This file and the skill guides in `.ai/skills/` define the project's conventions. All AI agents (Copilot, Cursor, Claude, etc.) must follow these rules.

> **Note**: This is a template. The project root folder name varies (e.g., `my-api`, `ecommerce-backend`). References to `django-template` are placeholders.

---

## Skills (Step-by-Step Guides)

Read the relevant skill before implementing any feature:

| Task | File |
|------|------|
| Create a new app/feature module | `.ai/skills/scaffold-app.md` |
| Add a model | `.ai/skills/add-model.md` |
| Add an API endpoint | `.ai/skills/add-endpoint.md` |
| Add or fix a serializer | `.ai/skills/add-serializer.md` |
| Write tests | `.ai/skills/write-tests.md` |

---

## Technology Stack

- Django 5.1.4 + Django REST Framework 3.15.2
- JWT auth: `djangorestframework-simplejwt`
- API docs: `drf-yasg` (Swagger/OpenAPI)
- Filtering: `django-filter`
- OTP: `pyotp`
- Tests: `pytest-django` + `factory-boy`
- Email: `django-anymail` (SendGrid in prod), console in dev

---

## Project Structure

```
apps/                     ← ALL Django apps live here
  common/                 ← Shared: BaseModel, permissions, utils, email, pagination
  users/                  ← User model + auth endpoints
  <your_app>/             ← Feature apps follow the same structure as users/
config/
  settings/
    base.py               ← Shared settings
    local.py              ← Dev overrides (debug toolbar, N+1 detection)
    prod.py               ← Production (gunicorn, whitenoise, SSL)
    test.py               ← Test overrides (in-memory email, tmpdir media)
  urls.py                 ← Root URL config
  api_urls.py             ← All API routes (app_name = "api")
requirements/
  base.txt                ← Core dependencies
  local.txt               ← Dev dependencies
  prod.txt                ← Production dependencies
.ai/skills/               ← AI skill guides (read before implementing)
```

---

## Non-Negotiable Rules

### 1. Models MUST inherit from BaseModel

```python
# CORRECT
from apps.common.models import BaseModel

class Product(BaseModel):
    name = models.CharField(max_length=255)

# WRONG — never do this
class Product(models.Model):
    id = models.UUIDField(...)  # don't redefine what BaseModel provides
    name = models.CharField(max_length=255)
```

BaseModel provides: `id` (UUID PK), `created_at`, `updated_at`, `is_active`, `activate()`, `deactivate()`.

### 2. Apps MUST live in `apps/`

```bash
# Create a new app
python manage.py startapp products apps/products

# Register in config/settings/base.py
LOCAL_APPS = [
    "apps.users.apps.UsersConfig",
    "apps.common",
    "apps.products.apps.ProductsConfig",  # add here
]
```

### 3. Views MUST have explicit permission_classes

```python
# CORRECT
class ProductView(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

# WRONG — never rely on global defaults
class ProductView(ListModelMixin, GenericViewSet):
    pass
```

### 4. Password fields MUST be write_only

```python
# CORRECT
password = serializers.CharField(min_length=6, write_only=True)

# WRONG
password = serializers.CharField(min_length=6)
```

### 5. API URLs MUST go through `config/api_urls.py`

```python
# config/api_urls.py
app_name = "api"
urlpatterns = [
    path("", include("apps.users.urls")),
    path("", include("apps.products.urls")),  # add here
]
```

---

## Standard ViewSet Pattern

```python
from rest_framework.mixins import (
    CreateModelMixin, DestroyModelMixin,
    ListModelMixin, RetrieveModelMixin, UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .models import Product
from .serializers import ProductSerializer, ProductWriteSerializer


class ProductView(
    CreateModelMixin,    # POST   /api/products/
    RetrieveModelMixin,  # GET    /api/products/<id>/
    UpdateModelMixin,    # PATCH  /api/products/<id>/
    DestroyModelMixin,   # DELETE /api/products/<id>/
    ListModelMixin,      # GET    /api/products/
    GenericViewSet,
):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_active", "status"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "price"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

---

## Standard Serializer Patterns

```python
from rest_framework import serializers
from .models import Product


# READ serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "status", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


# WRITE serializer (different fields for input)
class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "price", "status"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value
```

---

## Standard URL Pattern

```python
# apps/products/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ProductView

router = DefaultRouter()
router.register("products", ProductView, basename="products")

urlpatterns = [
    path("", include(router.urls)),
]
```

Auto-generated URL names:
- `api:products-list` → `GET /api/products/`
- `api:products-detail` → `GET/PATCH/DELETE /api/products/<id>/`

---

## Standard Test Pattern

```python
# apps/products/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


class TestProductView:
    def test_list(self, api_client_auth, user):
        ProductFactory.create_batch(3)
        client = api_client_auth(user)

        resp = client.get(reverse("api:products-list"))

        assert resp.status_code == status.HTTP_200_OK
        assert "results" in resp.json()

    def test_create(self, api_client_auth, user):
        client = api_client_auth(user)

        resp = client.post(reverse("api:products-list"), {"name": "Widget", "price": "9.99"})

        assert resp.status_code == status.HTTP_201_CREATED

    def test_unauthenticated(self, api_client):
        resp = api_client.get(reverse("api:products-list"))

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
```

---

## Common Utilities

```python
# OTP
from apps.common.utils import OTPUtils
code, token = OTPUtils.generate_otp(user, life=600)
OTPUtils.verify_otp(code, secret, life=600)

# Email
from apps.common.email import send_email
send_email(to_email="user@example.com", subject="Subject", message="Body")

# Pagination
from apps.common.pagination import DefaultPagination  # 20/page
from apps.common.pagination import LargePagination    # 1000/page
```

---

## Response Format

`CustomRenderer` wraps all responses:
- Success: `{"data": {...}, "error": null}`
- Error: `{"data": null, "error": {"status_code": 400, "message": "...", "details": []}}`

---

## Auth Endpoints (already implemented)

```
POST /api/auth/signup/          → Register (AllowAny)
POST /api/auth/login/           → JWT login (AllowAny)
POST /api/auth/refresh-token/   → Refresh access token (AllowAny)
POST /api/auth/forget-password/ → Request OTP reset (AllowAny)
POST /api/auth/reset-password/  → Reset with OTP (AllowAny)
POST /api/auth/change-password/ → Change password (IsAuthenticated)
GET  /api/users/me/             → Current user profile (IsAuthenticated)
```

---

## Dev Commands

```bash
# Setup
python -m venv env
source env/bin/activate        # Mac/Linux
env\scripts\activate           # Windows
pip install -r requirements/local.txt

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver

# Tests
pytest                                      # All tests
pytest apps/<appname>/                      # Single app
pytest -v                                   # Verbose
pytest -k "test_name"                       # Specific test
pytest --reuse-db                           # Reuse test DB (faster)
```

---

## DO's and DON'Ts

### DO
- Inherit all models from `BaseModel`
- Put all apps in `apps/`
- Set `permission_classes` explicitly on every view
- Use `write_only=True` on all password fields
- Use `get_serializer_class()` for separate read/write serializers
- Scope querysets in `get_queryset()` to the current user
- Document all endpoints with `@swagger_auto_schema`
- Write tests for every endpoint
- Use factories for test data

### DON'T
- Define `id`, `created_at`, `updated_at` manually (inherited)
- Use auto-increment integer PKs
- Use `username` field (use `email`)
- Create apps outside `apps/` directory
- Expose passwords in serializer output
- Hardcode secrets — use environment variables
- Skip tests
