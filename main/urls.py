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
    # path("review/like")
    # Profile
    path("profile", views.ProfileView.as_view(), name="profile"),
    path("myproducts", views.MyProductsView.as_view(), name="myproducts"),
    path("mybrands", views.MyBrandsView.as_view(), name="mybrands"),
]

urlpatterns += router.urls
