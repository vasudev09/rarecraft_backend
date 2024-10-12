from django.core.management.base import BaseCommand
from main.models import Product, Brand, Category
import requests


class Command(BaseCommand):
    help = "Performs link analysis on products and brands."

    def handle(self, *args, **kwargs):
        self.stdout.write("Started Cron Job for Link Analysis")

        products = Product.objects.only("slug")
        brands = Brand.objects.only("slug")
        categories = Category.objects.only("slug")

        base_url = "https://rarecraft.onrender.com"

        static_paths = ["/", "/products", "/signin", "/register", "/contact"]

        for path in static_paths:
            try:
                url = f"{base_url}{path}"
                response = requests.head(url, timeout=15)
                if response.status_code != 200:
                    self.stdout.write(f"\033[91mBroken link found: {url}\033[0m")
                else:
                    self.stdout.write(f"Status 200: {url}")
            except requests.RequestException as e:
                self.stdout.write(f"\033[91mError checking link for {path}: {e}\033[0m")

        # dynamic_paths
        for product in products:
            try:
                product_url = f"{base_url}/product/{product.slug}"
                response = requests.head(product_url, timeout=6)
                if response.status_code != 200:
                    self.stdout.write(
                        f"\033[91mBroken link found: {product_url}\033[0m"
                    )
                else:
                    self.stdout.write(f"Status 200: {product_url}")
            except requests.RequestException as e:
                self.stdout.write(
                    f"\033[91mError checking link for product {product.slug}: {e}\033[0m"
                )

        for brand in brands:
            try:
                brand_url = f"{base_url}/brand/{brand.slug}"
                response = requests.head(brand_url, timeout=6)
                if response.status_code != 200:
                    self.stdout.write(f"\033[91mBroken link found: {brand_url}\033[0m")
                else:
                    self.stdout.write(f"Status 200: {brand_url}")
            except requests.RequestException as e:
                self.stdout.write(
                    f"\033[91mError checking link for brand {brand.slug}: {e}\033[0m"
                )

        for brand in brands:
            try:
                brand_products_url = f"{base_url}/products/brand/{brand.slug}"
                response = requests.head(brand_products_url, timeout=6)
                if response.status_code != 200:
                    self.stdout.write(
                        f"\033[91mBroken link found: {brand_products_url}\033[0m"
                    )
                else:
                    self.stdout.write(f"Status 200: {brand_products_url}")
            except requests.RequestException as e:
                self.stdout.write(
                    f"\033[91mError checking link for brand products {brand.slug}: {e}\033[0m"
                )

        for category in categories:
            try:
                category_products_url = f"{base_url}/products/category/{category.slug}"
                response = requests.head(category_products_url, timeout=6)
                if response.status_code != 200:
                    self.stdout.write(
                        f"\033[91mBroken link found: {category_products_url}\033[0m"
                    )
                else:
                    self.stdout.write(f"Status 200: {category_products_url}")
            except requests.RequestException as e:
                self.stdout.write(
                    f"\033[91mError checking link for category products {category.slug}: {e}\033[0m"
                )

        self.stdout.write(self.style.SUCCESS("Link analysis completed."))
