# Django Template Project - Copilot Instructions

## Project Overview
This is a Django REST API project template using Django 5.1+ with Django REST Framework. It provides user authentication, JWT tokens, and a modular app structure.

> **Note**: This is a template project. The root folder name will vary based on the actual project name (e.g., `my-api-project`, `ecommerce-backend`, etc.). All references to "django-template" in this document should be understood as placeholders for the actual project name.

## Technology Stack
- **Backend**: Django 5.1.4, Django REST Framework 3.15.2
- **Authentication**: djangorestframework-simplejwt 5.4.0
- **Database**: SQLite (default), with support for other databases via django-environ
- **API Documentation**: drf-yasg (Swagger/OpenAPI)
- **Testing**: pytest with pytest-django and factory-boy
- **Additional**: django-filter, django-cors-headers, pyotp, Pillow

## Project Structure Conventions

### Directory Organization
```
<project-root>/                # Project name will vary (e.g., my-api-project/)
├── apps/                      # All Django apps live here
│   ├── common/               # Shared utilities, base models, permissions
│   ├── users/                # User management app
│   └── templates/            # Django templates
├── config/                   # Project configuration
│   ├── settings/             # Split settings (base, local, prod, test)
│   ├── urls.py              # Main URL configuration
│   └── api_urls.py          # API URL routing
└── requirements/             # Split requirements files
```

### Apps Structure
- **Location**: All apps MUST be in the `apps/` directory
- **Registration**: Apps are registered in settings as `apps.appname.apps.AppnameConfig`
- Each app should contain:
  - `models.py` - Database models
  - `views.py` - ViewSets and API views
  - `serializers.py` - DRF serializers
  - `urls.py` - App-specific URL routing
  - `admin.py` - Django admin configuration
  - `tests/` - Test directory with factories and test files
  - `migrations/` - Database migrations

## Code Conventions

### Models
1. **Base Model**: All models MUST inherit from `apps.common.models.BaseModel`
   - Provides: `id` (UUID primary key), `created_at`, `updated_at`, `is_active`
   - UUID fields are used for primary keys, not auto-incrementing integers
2. **User Model**: Custom user model at `apps.users.models.User`
   - Uses email as USERNAME_FIELD (not username)
   - Inherits from `AbstractBaseUser`, `PermissionsMixin`, and `BaseModel`
   - Has custom `UserManager` for user creation
3. **Soft Delete**: Use `deleted` field (Boolean) for soft deletes when needed
4. **Ordering**: Default ordering should be specified in model Meta (e.g., `ordering = ("created_at",)`)

### Views & ViewSets
1. **ViewSets**: Prefer using DRF ViewSets with mixins for API endpoints
   ```python
   from rest_framework.viewsets import GenericViewSet
   from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
   ```
2. **Generic Views**: Use `CreateAPIView`, `UpdateAPIView` for specific actions
3. **Custom Actions**: Use `@action` decorator for custom endpoints
4. **Documentation**: Use `@swagger_auto_schema` for API documentation
5. **Permissions**: Set `permission_classes` explicitly on each view/viewset
6. **Filtering**: Support `filterset_fields` and `search_fields` on viewsets
7. **Authentication**: Default authentication is JWT via `IsAuthenticated` permission

### Serializers
1. **Naming**: Serializers should end with `Serializer` (e.g., `UserSerializer`)
2. **Response Serializers**: Create separate response serializers when needed (e.g., `SignupResponseSerializer`)
3. **Validation**: Custom validation methods should follow pattern `validate_<field_name>`
4. **Password Fields**: Always use `write_only=True` for password fields
5. **Swagger Documentation**: Use `@swagger_serializer_method` for custom SerializerMethodFields

### URLs
1. **API URLs**: API endpoints are routed through `config/api_urls.py`
2. **Routers**: Use `DefaultRouter` for ViewSet registration
3. **Namespacing**: API URLs use `app_name = "api"` namespace
4. **URL Names**: Follow pattern: `<app>-<action>` (e.g., `users-list`, `users-detail`)

### Testing
1. **Framework**: Use pytest with `pytest-django`
2. **Fixtures**: Define fixtures in `apps/conftest.py` and app-specific `conftest.py`
3. **Factories**: Use factory-boy for model factories in `tests/factories.py`
4. **Markers**: Use `pytestmark = pytest.mark.django_db` for database tests
5. **API Testing**: Use `APIClient` or custom `api_client_auth` fixture
6. **Test Structure**: Organize tests in classes (e.g., `TestUserView`)
7. **Naming**: Test methods should start with `test_` and describe the scenario

### Authentication & Security
1. **JWT Tokens**: Use SimpleJWT for token authentication
2. **OTP**: Use `apps.common.utils.OTPUtils` for OTP generation and verification
3. **Password Reset Flow**: 
   - Generate OTP code and token
   - Send email with code
   - Verify using token and code
4. **Permissions**: Custom permissions in `apps.common.permissions.py`
5. **Email**: Email utility in `apps.common.email.py`

### Settings
1. **Split Settings**: Use environment-based settings (base, local, prod, test)
2. **Environment Variables**: Use `django-environ` for configuration
3. **Settings Structure**:
   - `DJANGO_APPS` - Core Django apps
   - `THIRD_PARTY_APPS` - External packages
   - `LOCAL_APPS` - Project apps
   - `INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS`
4. **Database**: Use `env.db()` for database configuration
5. **Paths**: Use `BASE_DIR` and `APPS_DIR` for path construction

### REST Framework Configuration
1. **Pagination**: Use `apps.common.pagination.DefaultPagination` (20 items per page)
2. **Filtering**: Enable DjangoFilterBackend, SearchFilter, and CustomOrderingFilter
3. **Authentication**: JWT via `rest_framework_simplejwt.authentication.JWTAuthentication`
4. **Permissions**: Default is `IsAuthenticated`

## Common Utilities

### BaseModel Methods
- `activate()` - Set is_active to True
- `deactivate()` - Set is_active to False
- UUID primary keys automatically generated

### OTPUtils Class
- `generate_otp(user, life=600)` - Generate OTP code and token
- `verify_otp(code, secret, life=600)` - Verify OTP code
- `generate_token(data)` - Generate base32 encoded token
- `decode_token(token)` - Decode token to extract data

### CustomOrderingFilter
- Extends DRF's OrderingFilter with better schema documentation
- Use with `ordering_fields` on viewsets

## API Patterns

### Standard CRUD ViewSet Pattern
```python
class MyModelView(RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = MyModelSerializer
    queryset = MyModel.objects.all()
    filterset_fields = ["field1", "field2"]
    search_fields = ["field1", "field2"]
    ordering_fields = ["created_at", "updated_at"]
```

### Custom Action Pattern
```python
@swagger_auto_schema(method="GET", responses={200: MySerializer})
@action(detail=False, methods=["GET"])
def custom_endpoint(self, request):
    # Implementation
    return Response(data, status=status.HTTP_200_OK)
```

### Authentication Endpoints Pattern
- `auth/signup/` - User registration
- `auth/login/` - Token obtain (JWT)
- `auth/refresh-token/` - Token refresh
- `auth/forget-password/` - Initiate password reset
- `auth/reset-password/` - Complete password reset
- `auth/change-password/` - Change password for authenticated users

## Development Workflow

### Creating New Apps
1. Create app in `apps/` directory: `python manage.py startapp appname apps/appname`
2. Add `apps.appname.apps.AppnameConfig` to `LOCAL_APPS` in settings
3. Create models inheriting from `BaseModel`
4. Create serializers, views, and URL routing
5. Write tests with factories
6. Register in admin if needed

### Adding New Models
1. Inherit from `apps.common.models.BaseModel`
2. Use UUID for primary keys (inherited)
3. Include `created_at`, `updated_at`, `is_active` (inherited)
4. Add soft delete with `deleted = models.BooleanField(default=False)` if needed
5. Define `__str__` method
6. Set Meta options (ordering, verbose_name, etc.)
7. Run migrations: `python manage.py makemigrations && python manage.py migrate`

### Adding API Endpoints
1. Create serializer in `serializers.py`
2. Create view/viewset in `views.py` with swagger documentation
3. Register in `urls.py` using router or path
4. Include app URLs in `config/api_urls.py`
5. Write tests in `tests/test_views.py`

### Writing Tests
1. Create factory in `tests/factories.py`
2. Register factory in `conftest.py` with `pytest-factoryboy`
3. Write test class in `tests/test_*.py`
4. Use fixtures for common setup (user, auth client, etc.)
5. Test all CRUD operations and edge cases

## Important Notes

### DO's
- ✅ Always inherit models from `BaseModel`
- ✅ Use UUID primary keys (via BaseModel)
- ✅ Use email for user authentication (not username)
- ✅ Document APIs with `@swagger_auto_schema`
- ✅ Write tests for all new features
- ✅ Use factories for test data
- ✅ Use environment variables for configuration
- ✅ Split requirements by environment
- ✅ Use ViewSets with mixins for standard CRUD
- ✅ Set explicit permission classes on views

### DON'Ts
- ❌ Don't use auto-incrementing integer primary keys
- ❌ Don't create apps outside `apps/` directory
- ❌ Don't use username field (use email)
- ❌ Don't expose passwords in serializer responses
- ❌ Don't forget `write_only=True` on password fields
- ❌ Don't skip tests
- ❌ Don't hardcode configuration values
- ❌ Don't forget to register new apps in settings

## Git Workflow
- Main branch: `main` (production-ready)
- Development branch: `dev` (integration branch)
- Create feature branches from `dev`
- Create PR back to `dev` branch
- Use pre-commit hooks (configured in project)

## Commands Reference
```bash
# Setup
python -m venv env
source env/bin/activate  # Mac/Linux
env\scripts\activate     # Windows
pip install -r requirements/local.txt

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver

# Tests
pytest
pytest apps/appname/tests/
pytest -v  # Verbose
pytest -k test_name  # Run specific test
```

## File Naming Conventions
- Models: Singular, PascalCase (e.g., `User`, `BlogPost`)
- Views: PascalCase with suffix (e.g., `UserView`, `SignUpView`)
- Serializers: PascalCase with `Serializer` suffix
- Factories: PascalCase with `Factory` suffix
- Test files: `test_*.py` (e.g., `test_views.py`, `test_models.py`)
- URL names: lowercase with hyphens (e.g., `user-list`, `token-obtain`)
