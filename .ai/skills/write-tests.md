# Skill: Write Tests

Use this skill when writing tests for any new or existing feature. Tests live in `apps/<appname>/tests/` and use pytest + factory-boy.

---

## Test File Structure

```
apps/<appname>/tests/
    __init__.py
    factories.py       ← Model factories (test data generators)
    test_models.py     ← Model unit tests (optional)
    test_views.py      ← API endpoint tests (required for every endpoint)
    test_serializers.py ← Serializer unit tests (for complex serializers)
```

---

## Global Fixtures (always available, defined in `apps/conftest.py`)

```python
user            # User instance created with UserFactory(password=test_password)
test_password   # "something-a-bit-serious"
test_email      # "test@email.com"
token           # {"refresh": "...", "access": "..."} for `user`
otp_code        # (code, token) tuple for password reset flow
api_client      # Unauthenticated APIClient (autouse=True, available everywhere)
api_client_auth # Function fixture: api_client_auth(user) → authenticated APIClient
```

---

## Writing a Factory

In `apps/<appname>/tests/factories.py`:

```python
from factory import Faker, LazyAttribute, SubFactory, post_generation
from factory.django import DjangoModelFactory

from apps.<appname>.models import <ModelName>
from apps.users.tests.factories import UserFactory


class <ModelName>Factory(DjangoModelFactory):
    # Basic field generators
    title = Faker("sentence", nb_words=4)
    description = Faker("paragraph")
    price = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    quantity = Faker("random_int", min=1, max=100)
    is_featured = False

    # Choices field — use the actual choice value
    status = <ModelName>.Status.DRAFT

    # ForeignKey — use SubFactory
    owner = SubFactory(UserFactory)

    # Derived field
    slug = LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))

    # Post-generation hook (for M2M or custom setup)
    @post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.set(extracted)

    class Meta:
        model = <ModelName>
        django_get_or_create = ["title"]  # prevent duplicates on unique fields
```

**Common Faker providers:**
```python
Faker("email")                    # test@example.com
Faker("name")                     # John Doe
Faker("first_name")               # John
Faker("sentence", nb_words=4)     # "This is a title"
Faker("paragraph")                # Multiple sentences
Faker("text", max_nb_chars=200)   # Long text
Faker("url")                      # https://example.com
Faker("uuid4")                    # UUID string
Faker("date_time_this_year")      # datetime
Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
Faker("random_int", min=1, max=100)
Faker("boolean")
```

---

## Writing View Tests

In `apps/<appname>/tests/test_views.py`:

```python
import pytest
from django.urls import reverse
from rest_framework import status

from apps.<appname>.models import <ModelName>
from apps.<appname>.tests.factories import <ModelName>Factory

# Apply django_db marker to all tests in this file
pytestmark = pytest.mark.django_db


class Test<ModelName>ListView:
    """Tests for GET /api/<resource>/"""

    def test_list_returns_paginated_results(self, api_client_auth, user):
        <ModelName>Factory.create_batch(5)
        url = reverse("api:<resource>-list")
        client = api_client_auth(user)

        resp = client.get(url)
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert "results" in data
        assert "count" in data

    def test_list_requires_authentication(self, api_client):
        url = reverse("api:<resource>-list")

        resp = api_client.get(url)

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_filter_by_status(self, api_client_auth, user):
        <ModelName>Factory(status=<ModelName>.Status.PUBLISHED)
        <ModelName>Factory(status=<ModelName>.Status.DRAFT)
        url = reverse("api:<resource>-list")
        client = api_client_auth(user)

        resp = client.get(url, {"status": "published"})
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert all(item["status"] == "published" for item in data["results"])

    def test_list_search(self, api_client_auth, user):
        <ModelName>Factory(title="Unique Search Term")
        <ModelName>Factory(title="Other Item")
        url = reverse("api:<resource>-list")
        client = api_client_auth(user)

        resp = client.get(url, {"search": "Unique Search Term"})
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert data["count"] >= 1
        assert any("Unique" in item["title"] for item in data["results"])


class Test<ModelName>CreateView:
    """Tests for POST /api/<resource>/"""

    def test_create_success(self, api_client_auth, user):
        url = reverse("api:<resource>-list")
        client = api_client_auth(user)
        payload = {"title": "New Item", "description": "A description"}

        resp = client.post(url, data=payload)
        data = resp.json()

        assert resp.status_code == status.HTTP_201_CREATED
        assert data["title"] == payload["title"]
        assert "id" in data
        assert <ModelName>.objects.filter(title=payload["title"]).exists()

    def test_create_missing_required_field(self, api_client_auth, user):
        url = reverse("api:<resource>-list")
        client = api_client_auth(user)
        payload = {}  # missing required title

        resp = client.post(url, data=payload)

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_requires_authentication(self, api_client):
        url = reverse("api:<resource>-list")

        resp = api_client.post(url, data={"title": "Test"})

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class Test<ModelName>DetailView:
    """Tests for GET/PATCH/DELETE /api/<resource>/<id>/"""

    def test_retrieve(self, api_client_auth, user):
        obj = <ModelName>Factory()
        url = reverse("api:<resource>-detail", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.get(url)
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert data["id"] == str(obj.id)

    def test_retrieve_not_found(self, api_client_auth, user):
        import uuid
        url = reverse("api:<resource>-detail", args=(uuid.uuid4(),))
        client = api_client_auth(user)

        resp = client.get(url)

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_partial_update(self, api_client_auth, user):
        obj = <ModelName>Factory(title="Old Title")
        url = reverse("api:<resource>-detail", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.patch(url, data={"title": "New Title"})
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert data["title"] == "New Title"
        obj.refresh_from_db()
        assert obj.title == "New Title"

    def test_delete(self, api_client_auth, user):
        obj = <ModelName>Factory()
        url = reverse("api:<resource>-detail", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.delete(url)

        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not <ModelName>.objects.filter(id=obj.id).exists()
```

---

## Testing Custom Actions

```python
class Test<ModelName>CustomActions:
    def test_publish_action(self, api_client_auth, user):
        obj = <ModelName>Factory(status=<ModelName>.Status.DRAFT)
        url = reverse("api:<resource>-publish", args=(obj.id,))
        client = api_client_auth(user)

        resp = client.post(url)

        assert resp.status_code == status.HTTP_200_OK
        obj.refresh_from_db()
        assert obj.status == <ModelName>.Status.PUBLISHED

    def test_featured_list(self, api_client_auth, user):
        <ModelName>Factory(is_featured=True)
        <ModelName>Factory(is_featured=False)
        url = reverse("api:<resource>-featured")
        client = api_client_auth(user)

        resp = client.get(url)
        data = resp.json()

        assert resp.status_code == status.HTTP_200_OK
        assert all(item["is_featured"] for item in data)
```

---

## Testing Auth Endpoints (CreateAPIView pattern)

```python
class TestSomeAuthView:
    def test_success(self, api_client):
        url = reverse("api:some-action")
        data = {"email": "user@example.com", "code": "123456"}

        resp = api_client.post(url, data=data)

        assert resp.status_code == status.HTTP_200_OK
        assert "message" in resp.json()

    def test_invalid_input(self, api_client):
        url = reverse("api:some-action")

        resp = api_client.post(url, data={})

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
```

---

## Testing Email Sending

```python
from django.core import mail

def test_sends_email(self, api_client, user):
    url = reverse("api:forget-password")

    resp = api_client.post(url, data={"email": user.email})

    assert resp.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to

def test_no_email_for_unknown_address(self, api_client):
    url = reverse("api:forget-password")

    resp = api_client.post(url, data={"email": "unknown@example.com"})

    assert resp.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 0  # silent fail
```

---

## Testing Serializers Directly

In `apps/<appname>/tests/test_serializers.py`:

```python
import pytest

from apps.<appname>.serializers import <ModelName>WriteSerializer
from apps.<appname>.tests.factories import <ModelName>Factory

pytestmark = pytest.mark.django_db


class Test<ModelName>WriteSerializer:
    def test_valid_data(self):
        data = {"title": "Valid Title", "description": "Some text"}
        serializer = <ModelName>WriteSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_title_too_short(self):
        data = {"title": "AB"}  # less than 3 chars
        serializer = <ModelName>WriteSerializer(data=data)

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_missing_required_field(self):
        serializer = <ModelName>WriteSerializer(data={})

        assert not serializer.is_valid()
        assert "title" in serializer.errors
```

---

## Running Tests

```bash
# All tests
pytest

# Single app
pytest apps/<appname>/

# Single file
pytest apps/<appname>/tests/test_views.py

# Single class
pytest apps/<appname>/tests/test_views.py::Test<ModelName>ListView

# Single test
pytest apps/<appname>/tests/test_views.py::Test<ModelName>ListView::test_list_returns_paginated_results

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print output
pytest -s
```

---

## Checklist

- [ ] `pytestmark = pytest.mark.django_db` at top of every test file
- [ ] Tests organized in classes by endpoint/feature
- [ ] Factory exists for every model being tested
- [ ] Tests cover the happy path (success case)
- [ ] Tests cover validation errors (missing/invalid fields)
- [ ] Tests cover authentication (unauthenticated → 401)
- [ ] Tests cover authorization (wrong user can't access another's data)
- [ ] Database state verified with `obj.refresh_from_db()` after mutations
- [ ] Email tests check `mail.outbox` count and recipient
- [ ] All tests pass: `pytest apps/<appname>/`
