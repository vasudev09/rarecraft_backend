from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


# Customer
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    image = models.CharField()

    def __str__(self):
        return self.user.username


# Category
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    image = models.CharField()

    def __str__(self):
        return self.name


# Brand
class Brand(models.Model):
    vendor = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField()
    image = models.CharField()

    def __str__(self):
        return self.name


# Product
class ProductTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# Product
class Product(models.Model):
    vendor = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField()
    description = models.CharField()
    content = models.TextField(null=True, blank=True)
    slug = models.SlugField(unique=True)
    tags = models.ManyToManyField(
        ProductTag,
        blank=True,
        related_name="products",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    details = models.JSONField(default=list)
    images = ArrayField(models.CharField(), default=list)

    def __str__(self):
        return self.name


# Review
class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    review_by = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField()
    review = models.TextField()
    likes = ArrayField(models.PositiveIntegerField(), default=list)

    def __str__(self):
        return f"Review by {self.review_by} on {self.product.name}"
