from urllib.parse import urlparse
from django.core.exceptions import ValidationError


def validate_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("Seules les URLs http:// et https:// sont autorisées.")
