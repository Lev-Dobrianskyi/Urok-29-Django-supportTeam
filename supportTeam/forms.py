from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Report, Comment, Category


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('title', 'description', 'category', 'priority')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'secret')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['secret'].required = False
        self.fields['secret'].label = "Internal Note (Agents/Managers only)"


class AssignAgentForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('agent',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agent'].queryset = User.objects.filter(role='agent')