from django.shortcuts import render, get_object_or_404
from .models import FooterLink


def page_detail(request, slug):
    """Dynamic pages like About Us, Contact, Privacy Policy"""
    page = get_object_or_404(FooterLink, slug=slug, external_url__isnull=True)
    return render(request, "partials/page_detail.html", {"page": page})
