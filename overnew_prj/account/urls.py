from django.urls import path
from . import views

app_name = "account"

urlpatterns = [
    path("", views.splash, name="splash"),

    path("api/send-email-code/", views.send_signup_verification_code, name="send_email_code"),
    path("api/verify-email-code/", views.verify_signup_verification_code, name="verify_email_code"),

    path("signup/email-verify/", views.email_verify_view, name="email_verify"),

    path("signup/step1/", views.info_step1, name="info_step1"),
    path("signup/step2/", views.info_step2, name="info_step2"),
    path("signup/step3/", views.info_step3, name="info_step3"),
    path("signup/step4/", views.info_step4, name="info_step4"),
    path("signup/step5/", views.info_step5, name="info_step5"),
    path("signup/complete/", views.signup_complete, name="signup_complete"),

    path("api/signup/", views.api_signup, name="api_signup"),
    path("api/login/", views.api_login, name="api_login"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("settings/", views.settings_view, name="settings"),

    path("notifications/", views.notifications_view, name="notifications"),
    path("api/notifications/unread-count/", views.api_notification_unread_count, name="api_notification_unread_count"),
    path("api/notifications/read-all/", views.api_notification_read_all, name="api_notification_read_all"),
    path("api/notifications/<int:notif_id>/read/", views.api_notification_read, name="api_notification_read"),

    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("api/profile/update/", views.api_profile_update, name="api_profile_update"),
    path("api/account/delete/", views.api_delete_account, name="api_delete_account"),
]