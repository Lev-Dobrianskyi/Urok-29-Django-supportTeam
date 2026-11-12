from ..models import Report
from django.db.models import Q, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta


def get_filtered_reports(user, filters):
    queryset = Report.objects.all()

    if user.role == 'client':
        queryset = queryset.filter(author=user)
    elif user.role == 'agent':
        queryset = queryset.filter(Q(status='new') | Q(agent=user))

    status = filters.get('status')
    priority = filters.get('priority')
    category = filters.get('category')
    agent = filters.get('agent')
    date = filters.get('date')
    search = filters.get('search')
    sort = filters.get('sort')

    if status: queryset = queryset.filter(status=status)
    if priority: queryset = queryset.filter(priority=priority)
    if category: queryset = queryset.filter(category_id=category)
    if agent: queryset = queryset.filter(agent_id=agent)
    if date: queryset = queryset.filter(dateOfCreation__date=date)
    if search: queryset = queryset.filter(title__icontains=search)

    if sort == 'priority':
        queryset = queryset.annotate(
            priority_order=Case(
                When(priority='critical', then=0),
                When(priority='high', then=1),
                When(priority='medium', then=2),
                When(priority='low', then=3),
                output_field=IntegerField(),
            )
        ).order_by('priority_order')
    elif sort == 'date':
        queryset = queryset.order_by('-dateOfCreation')
    else:
        queryset = queryset.order_by('-dateOfCreation')

    return queryset


def get_allowed_transitions(user, report):
    allowed = []

    if user.role == 'client' and report.author != user:
        return allowed
    if user.role == 'agent' and report.agent != user:
        return allowed

    if user.role == 'client':
        if report.status == 'done':
            if timezone.now() - report.lastEditDate <= timedelta(days=3):
                allowed = ['inProgress', 'closed']
            else:
                allowed = ['closed']
        elif report.status in ['new', 'inProgress', 'awaiting']:
            allowed = ['closed']
        return allowed

    if report.status == 'new':
        allowed = ['inProgress', 'denied']
    elif report.status == 'inProgress':
        allowed = ['awaiting', 'denied']
    elif report.status == 'awaiting':
        allowed = ['inProgress', 'done', 'denied']
    elif report.status == 'done':
        allowed = ['inProgress', 'closed', 'denied']

    return allowed