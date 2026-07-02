from rest_framework import serializers


class CartItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    price = serializers.FloatField(min_value=0)
    qty = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        ref_name = "CartItem"


class SendOtpSerializer(serializers.Serializer):
    phone_number = serializers.RegexField(
        r"^\+?[0-9]{10,15}$",
        help_text="Digits only, optional leading +. 10-15 digits.",
    )
    cart_items = CartItemSerializer(many=True, allow_empty=False)
    delivery_address = serializers.CharField(max_length=1000)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class VerifyOtpSerializer(serializers.Serializer):
    phone_number = serializers.RegexField(r"^\+?[0-9]{10,15}$")
    otp_entered = serializers.RegexField(r"^[0-9]{6}$")
