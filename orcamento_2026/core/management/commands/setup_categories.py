import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from orcamento_2026.core.models import Category, SubCategory


class Command(BaseCommand):
    help = "Load categories from a JSON file"

    def handle(self, *args, **kwargs):
        json_path = os.path.join(settings.BASE_DIR, "categories.json")

        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"File not found: {json_path}"))
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            cat_name = entry["category"]
            subcats = entry["subcategories"]

            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Category: {cat_name}"))

            for sub_name in subcats:
                sub, created = SubCategory.objects.get_or_create(name=sub_name, category=category)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"  -> Created SubCategory: {sub_name}"))

        self.stdout.write(self.style.SUCCESS("Categories setup complete!"))
