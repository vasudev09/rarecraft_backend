from rest_framework import generics
from . import serializers
from . import models
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from decouple import config
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from rest_framework.decorators import permission_classes, api_view
from django.db import IntegrityError
from rest_framework.views import APIView
from django.db.models import Q
from django.utils.text import slugify
from supabase import create_client, Client
import json
from random import choice, shuffle


# Initialize Supabase client
SUPABASE_URL = config("SUPABASE_URL")
SUPABASE_KEY = config("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_supabase(files, folder_type, id):
    public_urls = []

    for index, file in enumerate(files):
        folder_path = f"{folder_type}/{id}/{index}_{file.name}"

        response = supabase.storage.from_("assets").upload(
            file=file.read(),
            path=folder_path,
            file_options={"content-type": file.content_type},
        )
        if response.is_error:
            raise ValueError(
                f"Failed to upload image '{file.name}' to Supabase: {response['error']['message']}"
            )

        public_url = supabase.storage.from_("assets").get_public_url(folder_path)
        public_urls.append(public_url)

    return public_urls


def delete_supabase(folder_type, id):
    folder_path = f"{folder_type}/{id}/"
    response = supabase.storage.from_("assets").list(folder_path)

    for file_info in response:
        file_name = file_info["name"]
        supabase.storage.from_("assets").remove([f"{folder_path}{file_name}"])


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("name")
    email = request.data.get("email")
    password = request.data.get("password")
    if not all([username, email, password]):
        return Response({"message": "All fields are required."}, status=400)
    if len(username) < 3 or len(username) > 30:
        return Response(
            {"message": "Username must be between 3 and 30 characters."}, status=400
        )
    if len(email) < 5 or len(email) > 50:
        return Response(
            {"message": "Email must be between 5 and 50 characters."}, status=400
        )
    if len(password) < 8:
        return Response(
            {"message": "Password must be at least 8 characters."}, status=400
        )
    if User.objects.filter(email=email).exists():
        return Response({"message": "Email already exists."}, status=400)
    try:
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        customer = models.Customer.objects.create(
            user=user, image="https://cdn-icons-png.flaticon.com/128/236/236831.png"
        )
        try:
            send_mail(
                "Registration Successful!",
                "Welcome to RareCraft. Thank you for registering with us.",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except BadHeaderError:
            print("Invalid header found.")
        except Exception as e:
            print(f"Failed to send email: {e}")

        refresh = RefreshToken.for_user(user)
        response = Response(
            {"message": "Success", "customer_id": customer.id}, status=201
        )
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=604800,
        )
        return response
    except IntegrityError:
        return Response({"message": "Username already exists."}, status=400)
    except Exception as e:
        return Response({"message": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    User = get_user_model()
    if not all([email, password]):
        return Response({"message": "All fields are required."}, status=400)
    try:
        user = User.objects.get(email=email)
        username = user.username
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            response = Response(
                {"message": "Success", "username": user.username}, status=200
            )
            response.set_cookie(
                key="access_token",
                value=str(refresh.access_token),
                httponly=True,
                secure=True,
                samesite="None",
                max_age=604800,
            )
            return response
        else:
            msg = {"message": "Invalid Email/Password!!"}
            return Response(msg, status=401)

    except User.DoesNotExist:
        msg = {"message": "Invalid Email/Password!!"}
        return Response(msg, status=401)


@api_view(["GET"])
def logout(request):
    response = Response({"message": "Successfully logged out."}, status=200)
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=True,
        samesite="None",
        max_age=0,
        path="/",
    )
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def validate_user(request):
    token = request.COOKIES.get("access_token")
    if not token:
        return Response({"message": "No access token"}, status=401)
    try:
        validated_token = AccessToken(token)
        user_id = validated_token["user_id"]
        try:
            user = User.objects.get(id=user_id)
            return Response(
                {"message": "success", "username": user.username}, status=200
            )
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)
    except (InvalidToken, TokenError) as e:
        return Response({"message": "Invalid or expired token"}, status=401)


class ProfileView(APIView):
    def get(self, request):
        try:
            customer = models.Customer.objects.get(user=request.user)
            serializer = serializers.CustomerSerializer(customer)
            return Response(serializer.data, status=200)
        except models.Customer.DoesNotExist:
            return Response({"message": "Profile not found."}, status=404)
        except Exception as e:
            return Response({"message": str(e)}, status=500)

    def post(self, request):
        try:
            customer = models.Customer.objects.get(user=request.user)
            user = customer.user
            data = request.data.copy()
            if "email" in data:
                data.pop("email")
            username = data.get("username")
            password = data.get("password")

            if username:
                if len(username) < 3 or len(username) > 30:
                    return Response(
                        {"message": "Username must be between 3 and 30 characters."},
                        status=400,
                    )

            if password:
                if len(password) < 8:
                    return Response(
                        {"message": "Password must be at least 8 characters."},
                        status=400,
                    )

            # Update username, mobile, and image
            serializer = serializers.CustomerSerializer(
                customer, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save()

                if username:
                    user.username = username
                    user.save()
                if password:
                    user.set_password(password)
                    user.save()

                return Response(
                    {"message": "Profile updated successfully."}, status=200
                )
            return Response(serializer.errors, status=400)
        except models.Customer.DoesNotExist:
            return Response({"message": "Profile not found."}, status=404)
        except Exception as e:
            return Response({"message": str(e)}, status=500)


class MyProductsView(generics.ListAPIView):
    serializer_class = serializers.ProductSerializer

    def get_queryset(self):
        return models.Product.objects.filter(vendor__user=self.request.user)


class MyBrandsView(generics.ListAPIView):
    serializer_class = serializers.BrandSerializer

    def get_queryset(self):
        return models.Brand.objects.filter(vendor__user=self.request.user)


class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = models.Category.objects.all()

    def get_queryset(self):
        queryset = list(models.Category.objects.all())
        shuffle(queryset)
        return queryset

    serializer_class = serializers.CategorySerializer


class BrandListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = models.Brand.objects.all()

    def get_queryset(self):
        queryset = list(models.Brand.objects.all())
        shuffle(queryset)
        return queryset

    serializer_class = serializers.BrandSerializer


class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductSerializer

    # filters
    def get_queryset(self):
        queryset = (
            models.Product.objects.select_related("category", "brand")
            .prefetch_related("tags")
            .all()
        )

        if "search" in self.request.GET and self.request.GET["search"]:
            search_query = self.request.GET["search"]
            queryset = queryset.filter(Q(name__icontains=search_query))

        if "tag" in self.request.GET and self.request.GET["tag"]:
            tag = self.request.GET["tag"]
            queryset = queryset.filter(tags__name__icontains=tag)

        if "category" in self.request.GET and self.request.GET["category"]:
            category_slug = self.request.GET["category"]
            queryset = queryset.filter(category__slug=category_slug)

        if "brand" in self.request.GET and self.request.GET["brand"]:
            brand_slug = self.request.GET["brand"]
            queryset = queryset.filter(brand__slug=brand_slug)

        if "min_price" in self.request.GET and self.request.GET["min_price"]:
            min_price = self.request.GET["min_price"]
            queryset = queryset.filter(price__gte=min_price)

        if "max_price" in self.request.GET and self.request.GET["max_price"]:
            max_price = self.request.GET["max_price"]
            queryset = queryset.filter(price__lte=max_price)

        if "sortby" in self.request.GET and self.request.GET["sortby"]:
            sort_by = self.request.GET["sortby"]
            if sort_by == "alphabetic":
                queryset = queryset.order_by("name")
            elif sort_by == "price_htl":
                queryset = queryset.order_by("-price")
            elif sort_by == "price_lth":
                queryset = queryset.order_by("price")
            elif sort_by == "latest":
                queryset = queryset.order_by("-created_at")

        return queryset


class ProductView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return super().get_permissions()

    def get(self, request):
        slug = request.query_params.get("slug")
        if not slug:
            return Response({"message": "Slug is required"}, status=400)
        try:
            product = models.Product.objects.get(slug=slug)
            serializer = serializers.ProductSerializer(product)
            return Response(serializer.data, status=200)
        except models.Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=404)

    def post(self, request):
        name = request.data.get("name")
        description = request.data.get("description")
        content = request.data.get("content")
        brand_id = int(request.data.get("brand"))
        category_id = int(request.data.get("category"))
        price = float(request.data.get("price"))
        discount = float(request.data.get("discount"))
        details = request.data.get("details")
        image0 = request.data.get("image0")
        image1 = request.data.get("image1")
        image2 = request.data.get("image2")
        image3 = request.data.get("image3")

        if (
            not name
            or not description
            or not brand_id
            or not category_id
            or not price
            or not details
            or not image0
            or not image1
            or not image2
            or not image3
        ):
            return Response(
                {"message": "All fields are required"},
                status=400,
            )
        if len(name) < 6:
            return Response(
                {"message": "Product name must be above 5 characters"},
                status=400,
            )
        if price < 1:
            return Response(
                {"message": "Price must be above 0"},
                status=400,
            )
        if discount > 100:
            return Response(
                {"message": "Discount must not exceed 100"},
                status=400,
            )

        slug = slugify(name)
        if models.Product.objects.filter(slug=slug).exists():
            return Response(
                {"message": "Product with this name already exists"},
                status=400,
            )

        try:
            category = models.Category.objects.get(id=category_id)
        except models.Category.DoesNotExist:
            return Response({"message": "Category not found"}, status=400)

        try:
            brand = models.Brand.objects.get(id=brand_id)
        except models.Brand.DoesNotExist:
            return Response({"message": "Brand not found"}, status=400)

        try:
            customer = models.Customer.objects.get(user=request.user)
        except models.Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=403)

        try:
            product = models.Product.objects.create(
                vendor=customer,
                brand=brand,
                category=category,
                name=name,
                description=description,
                content=content,
                slug=slug,
                price=price,
                discount=discount,
                details=json.loads(details),
            )
        except Exception as e:
            return Response({"message": str(e)}, status=500)

        # Upload the images to Supabase
        try:
            image_urls = upload_supabase(
                [image0, image1, image2, image3], "products", product.id
            )
            product.images = image_urls
            product.save()
        except ValueError as e:
            product.delete()
            return Response({"message": str(e)}, status=500)
        except Exception as e:
            product.delete()
            return Response(
                {"message": f"An unexpected error occurred while uploading: {str(e)}"},
                status=500,
            )

        try:
            tags = models.ProductTag.objects.all()
            if tags.exists():
                selected_tag = choice(tags)
                product.tags.add(selected_tag)
        except Exception as e:
            print(f"Failed to select or add tag: {str(e)}")

        return Response({"message": "Product Created Successfully"}, status=201)

    def put(self, request):
        product_id = request.query_params.get("id")
        name = request.data.get("name")
        description = request.data.get("description")
        content = request.data.get("content")
        brand_id = int(request.data.get("brand"))
        category_id = int(request.data.get("category"))
        price = float(request.data.get("price"))
        discount = float(request.data.get("discount"))
        details = request.data.get("details")
        image0 = request.data.get("image0")
        image1 = request.data.get("image1")
        image2 = request.data.get("image2")
        image3 = request.data.get("image3")

        if not product_id:
            return Response(
                {"message": "Product ID is required"},
                status=400,
            )

        if (
            not name
            or not description
            or not brand_id
            or not category_id
            or not price
            or not details
        ):
            return Response(
                {"message": "All fields are required"},
                status=400,
            )
        if len(name) < 6:
            return Response(
                {"message": "Product name must be above 5 characters"},
                status=400,
            )
        if price < 1:
            return Response(
                {"message": "Price must be above 0"},
                status=400,
            )
        if discount > 100:
            return Response(
                {"message": "Discount must not exceed 100"},
                status=400,
            )

        slug = slugify(name)
        if models.Product.objects.exclude(id=product_id).filter(slug=slug).exists():
            return Response(
                {"message": "Product with this name already exists"},
                status=400,
            )

        try:
            product = models.Product.objects.get(id=product_id)
        except models.Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=400)

        try:
            category = models.Category.objects.get(id=category_id)
        except models.Category.DoesNotExist:
            return Response({"message": "Category not found"}, status=400)

        try:
            brand = models.Brand.objects.get(id=brand_id)
        except models.Brand.DoesNotExist:
            return Response({"message": "Brand not found"}, status=400)

        try:
            customer = models.Customer.objects.get(user=request.user)
        except models.Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=403)

        if product.vendor != customer:
            return Response(
                {"message": "You do not have permission to edit this product"},
                status=403,
            )

        if image0 and image1 and image2 and image3:
            try:
                delete_supabase("products", product.id)
                image_urls = upload_supabase(
                    [image0, image1, image2, image3], "products", product.id
                )
                product.images = image_urls
            except ValueError as e:
                return Response({"message": str(e)}, status=500)
            except Exception as e:
                return Response(
                    {
                        "message": f"An unexpected error occurred while uploading: {str(e)}"
                    },
                    status=500,
                )

        try:
            product.name = name
            product.description = description
            product.content = content
            product.category = category
            product.brand = brand
            product.price = price
            product.discount = discount
            product.details = json.loads(details)
            product.save()
        except Exception as e:
            return Response({"message": str(e)}, status=500)

        return Response({"message": "Product Updated Successfully"}, status=200)

    def delete(self, request):
        product_id = request.query_params.get("id")
        if not product_id:
            return Response({"message": "ID is required"}, status=400)
        try:
            product = models.Product.objects.get(id=product_id)
        except models.Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=404)

        try:
            customer = models.Customer.objects.get(user=request.user)
        except models.Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=403)

        if product.vendor != customer:
            return Response(
                {"message": "You do not have permission to delete this product"},
                status=403,
            )

        try:
            delete_supabase("products", product.id)
            product.delete()
            return Response({"message": "Product deleted successfully"}, status=200)
        except Exception as e:
            return Response(
                {"message": f"An unexpected error occurred while deleting: {str(e)}"},
                status=500,
            )


class BrandView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return super().get_permissions()

    def get(self, request):
        slug = request.query_params.get("slug")
        if not slug:
            return Response({"message": "Slug is required"}, status=400)
        try:
            brand = models.Brand.objects.get(slug=slug)
            serializer = serializers.BrandSerializer(brand)
            return Response(serializer.data, status=200)
        except models.Brand.DoesNotExist:
            return Response({"message": "Brand not found"}, status=404)

    def post(self, request):
        name = request.data.get("name")
        description = request.data.get("description")
        image_file = request.FILES.get("image")
        if not name or not description or not image_file:
            return Response(
                {"message": "All fields are required (name, description, image)"},
                status=400,
            )
        if len(name) < 3 or len(name) > 30:
            return Response(
                {"message": "Brand name must be between 3 and 30 characters."},
                status=400,
            )

        slug = slugify(name)
        if models.Brand.objects.filter(slug=slug).exists():
            return Response(
                {"message": "Brand with this name already exists"},
                status=400,
            )

        try:
            customer = models.Customer.objects.get(user=request.user)
        except models.Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=403)

        try:
            brand = models.Brand.objects.create(
                vendor=customer,
                name=name,
                slug=slug,
                description=description,
                image="https://cdn-icons-png.flaticon.com/512/16895/16895417.png",
            )
        except Exception as e:
            return Response({"message": str(e)}, status=500)

        # Upload the image to Supabase
        try:
            image_urls = upload_supabase([image_file], "brands", brand.id)
            brand.image = image_urls[0]
            brand.save()
        except ValueError as e:
            brand.delete()
            return Response({"message": str(e)}, status=500)
        except Exception as e:
            brand.delete()
            return Response(
                {"message": f"An unexpected error occurred while uploading: {str(e)}"},
                status=500,
            )

        return Response({"message": "Brand Created Successfully"}, status=201)

    def put(self, request):
        brand_id = request.query_params.get("id")
        if not brand_id:
            return Response({"message": "ID is required"}, status=400)
        try:
            brand = models.Brand.objects.get(id=brand_id)
        except models.Brand.DoesNotExist:
            return Response({"message": "Brand not found"}, status=404)

        if brand.vendor.user != request.user:
            return Response(
                {"message": "You do not have permission to update this brand"},
                status=403,
            )

        name = request.data.get("name")
        description = request.data.get("description")
        image_file = request.FILES.get("image")

        if name:
            if len(name) < 3 or len(name) > 30:
                return Response(
                    {"message": "Brand name must be between 3 and 30 characters."},
                    status=400,
                )
            slug = slugify(name)
            if models.Brand.objects.exclude(id=brand_id).filter(slug=slug).exists():
                return Response(
                    {"message": "Brand with this name already exists"},
                    status=400,
                )
            brand.name = name
            brand.slug = slug
        if description:
            brand.description = description
        if image_file:
            try:
                delete_supabase("brands", brand.id)
                image_urls = upload_supabase([image_file], "brands", brand.id)
                brand.image = image_urls[0]
            except ValueError as e:
                return Response({"message": str(e)}, status=500)
            except Exception as e:
                return Response(
                    {
                        "message": f"An unexpected error occurred while uploading: {str(e)}"
                    },
                    status=500,
                )

        brand.save()
        return Response({"message": "Brand Updated Successfully"}, status=200)

    def delete(self, request):
        brand_id = request.query_params.get("id")
        if not brand_id:
            return Response({"message": "ID is required"}, status=400)
        try:
            brand = models.Brand.objects.get(id=brand_id)
        except models.Brand.DoesNotExist:
            return Response({"message": "Brand not found"}, status=404)

        try:
            customer = models.Customer.objects.get(user=request.user)
        except models.Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=403)

        if brand.vendor != customer:
            return Response(
                {"message": "You do not have permission to delete this brand"},
                status=403,
            )

        try:
            delete_supabase("brands", brand.id)
            products = models.Product.objects.filter(brand=brand)
            for product in products:
                delete_supabase("products", product.id)
            brand.delete()
            return Response(
                {"message": "Brand and associated products deleted successfully"},
                status=200,
            )
        except Exception as e:
            return Response(
                {"message": f"An unexpected error occurred while deleting: {str(e)}"},
                status=500,
            )


class ReviewView(APIView):
    def post(self, request):
        product_id = request.data.get("product_id")
        review = request.data.get("review")
        rating = request.data.get("rating")
        if not product_id or not review or not rating:
            return Response({"message": "All fields are required"}, status=400)
        try:
            product = models.Product.objects.get(id=product_id)
        except models.Product.DoesNotExist:
            return Response({"message": "Invalid product ID"}, status=404)

        review_data = {
            "product": product.id,
            "review_by": request.user.username,
            "review": review,
            "rating": rating,
        }
        serializer = serializers.ReviewSerializer(data=review_data)

        if serializer.is_valid():
            serializer.save()
            updated_reviews = models.Review.objects.filter(product=product)
            reviews_serializer = serializers.ReviewSerializer(
                updated_reviews, many=True
            )
            return Response(
                {
                    "message": "Review Added successfully",
                    "reviews": reviews_serializer.data,
                },
                status=201,
            )

        return Response(serializer.errors, status=400)


@api_view(["GET"])
def like_review(request):
    review_id = request.query_params.get("id")
    if not review_id:
        return Response({"message": "Review ID is required"}, status=400)

    try:
        review = models.Review.objects.get(id=review_id)
    except models.Review.DoesNotExist:
        return Response({"message": "Review not found"}, status=404)

    try:
        customer = models.Customer.objects.get(user=request.user)
    except models.Customer.DoesNotExist:
        return Response({"message": "Customer not found"}, status=404)

    customer_id = customer.id
    if customer_id in review.likes:
        review.likes.remove(customer_id)
        message = "Like removed"
    else:
        review.likes.append(customer_id)
        message = "Like added"
    review.save()

    return Response({"message": message, "likes": review.likes}, status=200)
