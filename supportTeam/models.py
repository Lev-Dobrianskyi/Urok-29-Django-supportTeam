from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLES = (
        ('client', 'Client'),
        ('agent', 'Agent'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLES, default='client')

    def __str__(self):
        return f"{self.username} ({self.role})"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Report(models.Model):
    PRIORITIES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    STATUSES = (
        ('new', 'New'),
        ('inProgress', 'In progress'),
        ('awaiting', "Awaiting user's reply"),
        ('done', 'Done'),
        ('closed', 'Closed'),
        ('denied', 'Denied'),
    )

    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='reports')
    priority = models.CharField(max_length=15, choices=PRIORITIES, default='low')
    status = models.CharField(max_length=30, choices=STATUSES, default='new')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    dateOfCreation = models.DateTimeField(default=timezone.now)
    lastEditDate = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Comment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    dateOfCreation = models.DateTimeField(default=timezone.now)
    secret = models.BooleanField(default=False)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.report.title}"