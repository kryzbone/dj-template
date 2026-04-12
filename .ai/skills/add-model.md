# Skill: Add a Model

Use this skill when adding a new database model to an existing app. If you are creating a brand-new app, use `scaffold-app.md` instead.

---

## Prerequisites

- The app already exists in `apps/`
- The app is already registered in `config/settings/base.py`

---

## Step 1 — Define the Model

In `apps/<appname>/models.py`:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class <ModelName>(BaseModel):
    """
    One-line description of what this model represents.
    """

    # --- String / Text fields ---
    title = models.CharField(_("title"), max_length=255)
    body = models.TextField(_("body"), blank=True, default="")

    # --- Number fields ---
    quantity = models.PositiveIntegerField(_("quantity"), default=0)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2)

    # --- Boolean fields ---
    is_featured = models.BooleanField(_("is featured"), default=False)

    # --- Date / Time fields ---
    published_at = models.DateTimeField(_("published at"), null=True, blank=True)

    # --- Choice fields ---
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # --- Foreign key ---
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="<appname>_<modelname>s",
        verbose_name=_("owner"),
    )

    # --- Self-referential ---
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    # --- Many-to-many ---
    tags = models.ManyToManyField(
        "Tag",
        blank=True,
        related_name="<modelname>s",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("<model name>")
        verbose_name_plural = _("<model names>")
        # Optional: add database constraints
        # constraints = [
        #     models.UniqueConstraint(fields=["owner", "title"], name="unique_owner_title"),
        # ]

    def __str__(self) -> str:
        return self.title
```

### Field Rules

| Scenario | What to do |
|----------|-----------|
| Primary key | Never define `id` — inherited from `BaseModel` as UUID |
| Timestamps | Never define `created_at`/`updated_at` — inherited from `BaseModel` |
| Soft delete | Add `deleted = models.BooleanField(default=False)` |
| Active flag | Already provided as `is_active` by `BaseModel` |
| Nullable CharField | Use `blank=True, default=""` — avoid `null=True` on strings |
| Optional FK | Use `null=True, blank=True` |
| User ownership | FK to `"users.User"` with `on_delete=models.CASCADE` |
| Choices | Use inner `TextChoices`/`IntegerChoices` class on the model |
| Verbose names | Use `gettext_lazy` (`_`) on every field |

---

## Step 2 — Add Custom Manager (if needed)

Add a custom manager when you need reusable querysets:

```python
from django.db import models


class <ModelName>Manager(models.Manager):
    def active(self):
        return self.filter(is_active=True, deleted=False)

    def for_user(self, user):
        return self.filter(owner=user, is_active=True)


class <ModelName>(BaseModel):
    # ...
    objects = <ModelName>Manager()
```

---

## Step 3 — Add Model Methods (if needed)

```python
class <ModelName>(BaseModel):
    # ...

    def publish(self):
        """Publish this item."""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def archive(self):
        """Archive this item."""
        self.status = self.Status.ARCHIVED
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED
```

---

## Step 4 — Create and Run Migration

```bash
python manage.py makemigrations <appname>
python manage.py migrate
```

Verify the migration looks correct before applying:

```bash
python manage.py sqlmigrate <appname> <migration_number>
```

---

## Step 5 — Register in Admin

In `apps/<appname>/admin.py`:

```python
from django.contrib import admin

from .<models> import <ModelName>


@admin.register(<ModelName>)
class <ModelName>Admin(admin.ModelAdmin):
    list_display = ["__str__", "is_active", "created_at"]
    list_filter = ["is_active", "status"]       # add your choice fields
    search_fields = ["title"]                    # add your string fields
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ("-created_at",)

    # For models with many fields, use fieldsets:
    # fieldsets = (
    #     (None, {"fields": ("title", "body", "status")}),
    #     ("Metadata", {"fields": ("is_active", "created_at", "updated_at")}),
    # )
```

---

## Step 6 — Add Factory for Tests

In `apps/<appname>/tests/factories.py` (create the file if it doesn't exist):

```python
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from apps.<appname>.models import <ModelName>
from apps.users.tests.factories import UserFactory


class <ModelName>Factory(DjangoModelFactory):
    title = Faker("sentence", nb_words=4)
    body = Faker("paragraph")
    status = <ModelName>.Status.DRAFT
    # owner = SubFactory(UserFactory)  # uncomment if model has an owner

    class Meta:
        model = <ModelName>
```

**Factory field rules:**
- Use `Faker("email")`, `Faker("name")`, `Faker("sentence")`, `Faker("paragraph")`, etc.
- Use `SubFactory(RelatedFactory)` for ForeignKey fields
- Use `django_get_or_create` to prevent duplicate unique fields

---

## Step 7 — Write Model Tests (optional but recommended)

In `apps/<appname>/tests/test_models.py`:

```python
import pytest

from apps.<appname>.tests.factories import <ModelName>Factory

pytestmark = pytest.mark.django_db


class Test<ModelName>:
    def test_str(self):
        obj = <ModelName>Factory(title="My Title")
        assert str(obj) == "My Title"

    def test_activate_deactivate(self):
        obj = <ModelName>Factory(is_active=False)
        obj.activate()
        assert obj.is_active is True
        obj.deactivate()
        assert obj.is_active is False

    def test_default_is_active(self):
        obj = <ModelName>Factory()
        assert obj.is_active is True

    def test_uuid_primary_key(self):
        obj = <ModelName>Factory()
        # UUIDs are not integers
        assert not isinstance(obj.id, int)
```

---

## Checklist

- [ ] Model inherits from `BaseModel` (not `models.Model`)
- [ ] No `id`, `created_at`, `updated_at` fields defined (inherited)
- [ ] `__str__` returns a human-readable string
- [ ] `ordering` defined in `Meta`
- [ ] All user-visible strings use `gettext_lazy` (`_`)
- [ ] Nullable string fields use `blank=True, default=""` (not `null=True`)
- [ ] Migration created with `makemigrations` and applied with `migrate`
- [ ] Model registered in `admin.py`
- [ ] Factory created in `tests/factories.py`
