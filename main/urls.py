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
    path("product", views.ProductView.as_view(), name="product-detail"),
    path("products", views.ProductListView.as_view(), name="product-list"),
    path("brand", views.BrandView.as_view(), name="brand-detail"),
    path("brands", views.BrandListView.as_view(), name="brand-list"),
    path("categories", views.CategoryListView.as_view(), name="category-list"),
    path("review", views.ReviewView.as_view(), name="review-detail"),
    path("review/like", views.like_review, name="review-like"),
    # Profile
    path("profile", views.ProfileView.as_view(), name="profile"),
    path("myproducts", views.MyProductsView.as_view(), name="myproducts"),
    path("mybrands", views.MyBrandsView.as_view(), name="mybrands"),
    # slugs
    path("brand/slugs", views.brand_slugs, name="brands-slug-list"),
    path("product/slugs", views.product_slugs, name="products-slug-list"),
    path("category/slugs", views.category_slugs, name="categories-slug-list"),
    # cron
    path("run_link_analysis", views.run_link_analysis, name="rarecraft-link-analysis"),
]

urlpatterns += router.urls
