from rest_framework import serializers
from .models import Customer, Category, Brand, ProductTag, Product, Review
from django.contrib.auth.models import User


# User Serializer (for Customer)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


# Customer Serializer
class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "user", "mobile", "image"]


# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "image"]


# Brand Serializer
class BrandSerializer(serializers.ModelSerializer):
    vendor = CustomerSerializer(read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "vendor", "name", "slug", "description", "image"]


# ProductTag Serializer
class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ["id", "name"]


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "product", "review_by", "rating", "review", "likes"]


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    vendor = CustomerSerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = ProductTagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "brand",
            "category",
            "name",
            "description",
            "content",
            "slug",
            "tags",
            "price",
            "discount",
            "details",
            "reviews",
        ]
