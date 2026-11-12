from django.core.exceptions import ValidationError

def create_user(form):
    user = form.save(commit=False)
    user.role = 'client'
    user.save()
    return user

def update_user_profile(form):
    user = form.save(commit=False)
    user.save()
    return user