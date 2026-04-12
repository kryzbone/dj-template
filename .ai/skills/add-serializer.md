# Skill: Add or Fix a Serializer

Use this skill when adding new serializers, fixing validation, handling nested data, custom computed fields, or custom create/update logic.

---

## Serializer Types Used in This Project

| Type | When to use |
|------|------------|
| `ModelSerializer` | Standard CRUD serializer backed by a model |
| `Serializer` (plain) | Actions without a model (e.g., password reset, OTP verify) |
| Response serializer | When the response shape differs from the input/model shape |

---

## Pattern 1 — Standard Read Serializer

```python
from rest_framework import serializers

from .<models> import <ModelName>


class <ModelName>Serializer(serializers.ModelSerializer):
    class Meta:
        model = <ModelName>
        fields = [
            "id",
            "title",
            "description",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
```

---

## Pattern 2 — Write Serializer (create/update input)

```python
class <ModelName>WriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = <ModelName>
        fields = ["title", "description", "status"]

    def validate_title(self, value: str) -> str:
        """Single-field validation."""
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        """Cross-field validation."""
        if attrs.get("status") == "published" and not attrs.get("title"):
            raise serializers.ValidationError(
                {"title": "Title is required before publishing."}
            )
        return attrs
```

---

## Pattern 3 — Serializer with Computed Field

Use `SerializerMethodField` for read-only computed values:

```python
from drf_yasg.utils import swagger_serializer_method


class <ModelName>Serializer(serializers.ModelSerializer):
    full_info = serializers.SerializerMethodField()
    token = serializers.SerializerMethodField()

    class Meta:
        model = <ModelName>
        fields = ["id", "title", "full_info", "token"]

    def get_full_info(self, obj) -> str:
        return f"{obj.title} ({obj.status})"

    @swagger_serializer_method(serializer_or_field=serializers.JSONField())
    def get_token(self, obj):
        """Decorate with @swagger_serializer_method when return type is complex."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(obj)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
```

---

## Pattern 4 — Nested Serializer (read)

```python
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)  # nested read-only

    class Meta:
        model = Post
        fields = ["id", "title", "author", "created_at"]
```

---

## Pattern 5 — Writable Nested / FK Write via PK

```python
class PostWriteSerializer(serializers.ModelSerializer):
    # Accept a UUID to set the FK; respond with author_id in the output
    author_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Post
        fields = ["title", "author_id"]

    def validate_author_id(self, value):
        from apps.users.models import User
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Author not found.")
        return value

    def create(self, validated_data):
        author_id = validated_data.pop("author_id")
        return Post.objects.create(author_id=author_id, **validated_data)
```

---

## Pattern 6 — Password Handling

```python
class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, write_only=True)  # ALWAYS write_only
    password2 = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "password", "password2"]

    def validate_password2(self, value: str) -> str:
        if self.initial_data.get("password") != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def create(self, validated_data: dict):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)
```

**Rules:**
- `write_only=True` on every password field — no exceptions
- Never include password fields in `read_only_fields`
- Use `create_user()` to hash passwords properly

---

## Pattern 7 — Plain Serializer (no model)

For actions that don't map directly to a model (OTP, tokens, search, etc.):

```python
class VerifyOTPSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    code = serializers.CharField(min_length=6, max_length=6, required=True)

    def create(self, validated_data: dict):
        from apps.common.utils import OTPUtils

        token = validated_data["token"]
        code = validated_data["code"]

        data = OTPUtils.decode_token(token)
        if not data or not isinstance(data, dict):
            raise serializers.ValidationError("Invalid token.")

        if not OTPUtils.verify_otp(code, data["secret"]):
            raise serializers.ValidationError("Invalid or expired code.")

        return {"verified": True}
```

---

## Pattern 8 — Serializer with Request Context

Access the current request inside a serializer (e.g., to get the logged-in user):

```python
class <ModelName>Serializer(serializers.ModelSerializer):
    class Meta:
        model = <ModelName>
        fields = ["id", "title"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        return <ModelName>.objects.create(owner=user, **validated_data)
```

**Pass context from the view:**

```python
# In views.py — GenericViewSet does this automatically
# For manual calls:
serializer = MySerializer(data=request.data, context={"request": request})
```

---

## Pattern 9 — Response Serializer (different shape from model)

Use when the API response needs to include data beyond the model's direct fields:

```python
class SignupResponseSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "email", "token")

    @swagger_serializer_method(serializer_or_field=serializers.JSONField())
    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
```

**In the view — use a different serializer for the response:**

```python
def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)  # input serializer
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()

    response_serializer = SignupResponseSerializer(obj)  # output serializer
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
```

---

## Validation Error Format

Always raise `serializers.ValidationError` with a descriptive string or dict:

```python
# Single field error
raise serializers.ValidationError("Message for this specific field.")

# Named field error (shows up under the field key)
raise serializers.ValidationError({"field_name": "Message about this field."})

# Non-field / general error
raise serializers.ValidationError({"detail": "Something went wrong."})
```

---

## Checklist

- [ ] Read serializers have `id`, `created_at`, `updated_at` in `read_only_fields`
- [ ] Write serializers only include writable fields
- [ ] All password fields use `write_only=True`
- [ ] Single-field validation uses `validate_<fieldname>(self, value)`
- [ ] Cross-field validation uses `validate(self, attrs)`
- [ ] `SerializerMethodField` decorated with `@swagger_serializer_method` for complex types
- [ ] Plain `Serializer` used (not `ModelSerializer`) for non-model actions
- [ ] `context={"request": request}` passed when serializer needs request access
- [ ] Separate response serializer used when response shape differs from input
- [ ] ValidationError messages are clear and describe the actual problem
