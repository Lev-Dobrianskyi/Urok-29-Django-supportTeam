from django.core.exceptions import ValidationError

def save_category(user, form):
    if user.role != 'manager':
        raise ValidationError("Only managers can manage categories.")
    return form.save()

def delete_category(user, category):
    if user.role != 'manager':
        raise ValidationError("Only managers can manage categories.")
    category.delete()