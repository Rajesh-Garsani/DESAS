from django.db import models
from django.urls import reverse


class FooterSection(models.Model):
    """Sections like Quick Links, Customer Services"""
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    """Links under each section like Shop, About Us, etc."""
    section = models.ForeignKey(FooterSection, related_name="links", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Unique slug for internal page routing")
    content = models.TextField(blank=True, null=True, help_text="Page content to display")
    external_url = models.CharField(max_length=255, blank=True, null=True, help_text="Optional external link")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.section.title} - {self.name}"

    def get_url(self):
        """If external URL exists, use it; else use internal page URL"""
        if self.external_url:
            return self.external_url
        return reverse("footer:page_detail", kwargs={"slug": self.slug})
