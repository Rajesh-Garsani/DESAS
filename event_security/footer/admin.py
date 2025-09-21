from django.contrib import admin
from .models import FooterSection, FooterLink


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1


@admin.register(FooterSection)
class FooterSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    ordering = ("order",)
    inlines = [FooterLinkInline]


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "slug", "external_url", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("section", "order")
