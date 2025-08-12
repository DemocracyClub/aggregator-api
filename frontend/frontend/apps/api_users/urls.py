from django.contrib.auth import views as auth_views
from django.urls import path

from api_users import views

app_name = "api_users"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "authenticate/", views.AuthenticateView.as_view(), name="authenticate"
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="users/logout.html"),
        name="logout",
    ),
    path(
        "keys/<int:pk>/delete/",
        views.DeleteAPIKeyView.as_view(),
        name="delete-key",
    ),
    path(
        "keys/<int:pk>/refresh/",
        views.RefreshAPIKeyView.as_view(),
        name="refresh-key",
    ),
    path(
        "details",
        views.UpdateProfileDetailsView.as_view(),
        name="add_profile_details",
    ),
    path(
        "",
        views.ProfileView.as_view(),
        name="profile",
    ),
]
