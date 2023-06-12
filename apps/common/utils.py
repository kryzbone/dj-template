from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode
from rest_framework.filters import OrderingFilter


def encode_uid(pk):
    return force_str(urlsafe_base64_encode(force_bytes(pk)))


class CustomOrderingFilter(OrderingFilter):
    """Custom OrderingFilter with fields for description"""

    def get_schema_fields(self, view):
        check = hasattr(view, "ordering_fields")

        if check:
            fields = [f"`{field}`" for field in view.ordering_fields]
            reverse_fields = [f"`-{field}`" for field in view.ordering_fields]

            self.ordering_description = (
                f"Fields to use when ordering the results: {', '.join(fields)}. "
                f"The client may also specify reverse orderings by prefixing the field name "
                f"with `-`: {', '.join(reverse_fields)}."
            )

        return super().get_schema_fields(view)
