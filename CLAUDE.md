# Django Template — Project Guide for AI Agents

> This file is auto-loaded by Claude Code. For Cursor, see `.cursorrules`. For GitHub Copilot, see `.github/copilot-instructions.md`. All files point to the same conventions.

## Project Overview

Django 5.1 REST API template using Django REST Framework. All new features must follow the conventions described here. The skills in `.ai/skills/` are step-by-step recipes for common tasks.

## Skills (Task Recipes)

| Task | Skill File |
|------|-----------|
| Create a new Django app/feature module | `.ai/skills/scaffold-app.md` |
| Add a model to an existing app | `.ai/skills/add-model.md` |
| Add an API endpoint | `.ai/skills/add-endpoint.md` |
| Add or fix a serializer | `.ai/skills/add-serializer.md` |
| Write tests for a view or model | `.ai/skills/write-tests.md` |

**When a user asks you to add a feature, read the relevant skill file first before writing any code.**

## Critical Rules (Non-Negotiable)

1. **All models inherit from `apps.common.models.BaseModel`** — never from `models.Model` directly
2. **All apps live in `apps/`** — register as `apps.appname.apps.AppnameConfig` in settings
3. **UUID primary keys** — inherited from BaseModel, never use auto-increment integers
4. **Email is the username field** — never use Django's default `username`
5. **API URLs route through `config/api_urls.py`** — use `app_name = "api"` namespace
6. **Every view needs explicit `permission_classes`** — never rely on global defaults alone
7. **Password fields always use `write_only=True`** — never expose in responses
8. **Tests are mandatory** — every new endpoint and model needs tests

## Project Layout

```
apps/
  common/          ← BaseModel, permissions, utils, pagination, email helpers
  users/           ← User model, auth endpoints, JWT
  <new_app>/       ← Your feature apps go here
config/
  settings/
    base.py        ← Shared settings
    local.py       ← Dev overrides
    prod.py        ← Production overrides
    test.py        ← Test overrides
  urls.py          ← Root URL config
  api_urls.py      ← All API routes (app_name="api")
requirements/
  base.txt         ← Core deps
  local.txt        ← Dev deps (pytest, debug toolbar)
  prod.txt         ← Production deps (gunicorn, whitenoise)
```

## BaseModel (every model gets these for free)

```python
from apps.common.models import BaseModel

class MyModel(BaseModel):
    # Inherited automatically:
    # id          → UUIDField (primary key)
    # created_at  → DateTimeField (auto set on create)
    # updated_at  → DateTimeField (auto set on update)
    # is_active   → BooleanField (default True)
    # activate()  → sets is_active=True, saves
    # deactivate()→ sets is_active=False, saves
    pass
```

## Common Utilities

```python
# OTP generation & verification
from apps.common.utils import OTPUtils
code, token = OTPUtils.generate_otp(user, life=600)  # life in seconds
OTPUtils.verify_otp(code, secret, life=600)
OTPUtils.generate_token({"user_id": str(user.id)})
OTPUtils.decode_token(token)

# Email
from apps.common.email import send_email, send_email_template
send_email(to_email, subject, message)
send_email_template(user, template_id, {"key": "value"})

# Pagination
from apps.common.pagination import DefaultPagination   # 20/page, max 100
from apps.common.pagination import LargePagination    # 1000/page, max 10000
```

## Response Format

All API responses are wrapped by `CustomRenderer`:
- Success: `{"data": {...}, "error": null}`
- Error: `{"data": null, "error": {...}}`

Error format from `api_exception_handler`:
```json
{"status_code": 400, "message": "...", "details": []}
```

## JWT Authentication

- Header: `Authorization: Bearer <access_token>`
- Access token lifetime: 1 day
- Refresh token lifetime: 3 days
- Login endpoint: `POST /api/auth/login/` (email + password)
- Refresh endpoint: `POST /api/auth/refresh-token/`

## Testing Fixtures (available in all tests via `apps/conftest.py`)

```python
user           → User instance (with test_password)
test_password  → "something-a-bit-serious"
test_email     → "test@email.com"
token          → {"refresh": "...", "access": "..."}
otp_code       → (code, token) tuple
api_client     → Unauthenticated APIClient
api_client_auth→ Function: api_client_auth(user) → authenticated APIClient
```

## Running Tests

```bash
pytest                          # All tests
pytest apps/myapp/tests/        # Single app
pytest -k test_name             # Specific test
pytest -v                       # Verbose
```
