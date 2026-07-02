from django.urls import path

from .views import MenuView, SendOtpView, VerifyOtpView

urlpatterns = [
    path("menu/", MenuView.as_view(), name="menu"),
    path("send-otp/", SendOtpView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),
]
