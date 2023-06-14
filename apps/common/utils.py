import base64
import json
import logging

import pyotp
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode
from rest_framework.filters import OrderingFilter

User = get_user_model()


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


class OTPUtils:
    @classmethod
    def generate_token(cls, data):
        # strigify data
        data = json.dumps(data)
        # encode data with base32 encryption
        encoded = base64.b32encode(data.encode())
        return encoded.decode()

    @classmethod
    def generate_otp(cls, user: User, life=600):
        """Generates opt code

        Params:
            user: User object
            time: [optional] life sapn of otp in seconds. default: 600

        Returns:
            code: otp code
            token: Generated token for code verification

        """
        secret = pyotp.random_base32()
        data = {"user_id": str(user.id), "secret": secret}
        # generate token
        token = cls.generate_token(data)

        totp = pyotp.TOTP(secret, interval=life)
        return totp.now(), token

    @classmethod
    def decode_token(cls, token: str):
        """
        Decode token to extract data

        Params:
            token: token generated from otp generate

        Returns:
            data: dict data decoded from token or None
        """

        # encode token to byte
        token = token.encode()
        # decode token with base32. Returns byte
        decoded = base64.b32decode(token)
        # decode data from byte to string
        decoded = decoded.decode()
        # convert decoded data to dict
        try:
            data = json.loads(decoded)
        except Exception as e:
            logging.warning(e)
            return None
        return data

    @classmethod
    def verify_otp(cls, code, secret, life=600):
        """Verify otp code"""

        totp = pyotp.TOTP(secret, interval=life)
        return totp.verify(code)
