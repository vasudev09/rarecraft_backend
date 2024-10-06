from django.urls import path
from . import views
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    # Auth
    path("register", views.register, name="register"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("validate-user", views.validate_user, name="validate_user"),
    # App
    # path("product"),
    # path("products"),
    # path("brand"),
    # path("brands"),
    # path("categories"),
    # path("review"),
    # path("image"),
    # Profile
    path("profile", views.ProfileView.as_view(), name="profile"),
    # path("myproducts"),
    # path("mybrands"),
]

urlpatterns += router.urls
