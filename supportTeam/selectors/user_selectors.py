from ..models import User, Report
from django.db.models import Count

def get_agents():
    return User.objects.filter(role='agent')

def get_user_profile_context(user):
    context = {}
    if user.role == 'client':
        context['reports'] = Report.objects.filter(author=user)
    elif user.role == 'agent':
        context['reports'] = Report.objects.filter(agent=user)
        context['resolved_count'] = Report.objects.filter(agent=user, status__in=['done', 'closed']).count()
    elif user.role == 'manager':
        context['status_stats'] = Report.objects.values('status').annotate(count=Count('id'))
        context['agent_stats'] = User.objects.filter(role='agent').annotate(ticket_count=Count('assigned_reports'))
    return context