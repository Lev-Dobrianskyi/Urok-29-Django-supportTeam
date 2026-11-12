from ..models import Category

def get_all_categories():
    return Category.objects.all()