from .models import FooterSection

def footer_sections(request):
    return {
        "footer_sections": FooterSection.objects.prefetch_related("links").all()
    }
