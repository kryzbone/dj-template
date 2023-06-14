from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.email import send_email
from apps.common.utils import OTPUtils

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    """
    serializer for signing up a new user
    """

    password = serializers.CharField(min_length=6, write_only=True)
    password2 = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "password", "password2"]

    # Check if passwords match
    def validate_password2(self, password2: str):
        if self.initial_data.get("password") != password2:
            raise serializers.ValidationError("passwords do not match")
        return password2

    def create(self, validated_data: dict):
        # Remove second password field
        _ = validated_data.pop("password2")
        return User.objects.create_user(**validated_data)


class SignupResponseSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "email", "token")

    @swagger_serializer_method(
        serializer_or_field=serializers.JSONField(),
    )
    def get_token(self, user: User):
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "name", "id"]


class ForgotPasswordSerializer(serializers.Serializer):
    """
    serializer for initiating forgot password. Send reset code
    """

    email = serializers.EmailField(required=True)

    def create(self, validated_data: dict):
        """
        if email code to a user, send an email with a code to reset password
        """
        token = ""
        email = validated_data.get("email")
        if user := User.objects.filter(email=email).first():
            code, token = OTPUtils.generate_otp(user)

            # dynamic_data = {"first_name": user.first_name, "verification_code": code}
            send_email(email, "Password Reset", code)

        return {"token": token}


class ResetPasswordSerializer(serializers.Serializer):
    """ """

    token = serializers.CharField(required=True)
    code = serializers.CharField(min_length=6, required=True)
    password = serializers.CharField(min_length=6, required=True)

    def create(self, validated_data):
        """
        reset user password using email as an identification
        """

        token = validated_data.get("token")
        code = validated_data.get("code")
        password = validated_data.get("password")

        data = OTPUtils.decode_token(token)

        if not data or not isinstance(data, dict):
            raise serializers.ValidationError("Invalid token")

        if not (user := User.objects.filter(id=data.get("user_id")).first()):
            raise serializers.ValidationError("User does not exist")

        # validate code
        if not OTPUtils.verify_otp(code, data["secret"]):
            raise serializers.ValidationError("Invalid code")

        # reset password
        user.set_password(raw_password=password)
        user.save()

        return {
            "email": user.email,
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(min_length=6, required=True)
    new_password = serializers.CharField(min_length=6, required=True)

    class Meta:
        fields = ("old_password", "new_password")

    def create(self, validated_data):
        request = self.context.get("request")
        user: User = request.user

        if not user.check_password(validated_data.get("old_password")):
            raise serializers.ValidationError({"detail": "Incorrect password"})

        # reset password
        user.set_password(raw_password=validated_data.get("new_password"))
        user.save()

        return {"old_password": "", "new_password": ""}
