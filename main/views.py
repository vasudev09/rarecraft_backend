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


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")
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
        response = Response({"message": "Success", "user_id": customer.id}, status=201)
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
    email = request.POST.get("email")
    password = request.POST.get("password")
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
                {"message": "Success", "user": user.username}, status=200
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
        return Response({}, status=401)
    try:
        validated_token = AccessToken(token)
        user_id = validated_token["user_id"]
        return Response({}, status=200)
    except (InvalidToken, TokenError) as e:
        return Response({}, status=401)


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
            serializer = serializers.CustomerSerializer(
                customer, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Success"}, status=200)
            return Response(serializer.errors, status=400)
        except models.Customer.DoesNotExist:
            return Response({"message": "Profile not found."}, status=404)
        except Exception as e:
            return Response({"message": str(e)}, status=500)
