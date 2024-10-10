from rest_framework import serializers
from .models import Customer, Category, Brand, ProductTag, Product, Review
from django.contrib.auth.models import User
from django.db.models import Avg


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
    total_products = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id",
            "vendor",
            "name",
            "description",
            "slug",
            "image",
            "total_products",
            "reviews",
        ]

    def get_total_products(self, obj):
        return obj.products.count()

    def get_reviews(self, obj):
        avg_review = obj.products.aggregate(Avg("reviews__rating"))[
            "reviews__rating__avg"
        ]
        total_reviews = Review.objects.filter(product__brand=obj).count()
        return {
            "avg_review": avg_review if avg_review is not None else 0.0,
            "total_reviews": total_reviews,
        }


# ProductTag Serializer
class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ["id", "name"]


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "review_by",
            "rating",
            "review",
            "likes",
            "created_at",
        ]


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = ProductTagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
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
            "images",
        ]
