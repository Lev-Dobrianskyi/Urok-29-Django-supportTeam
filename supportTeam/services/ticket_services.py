from django.core.exceptions import ValidationError
from django.utils import timezone


def create_report(user, form):
    if user.role == 'client':
        open_tickets = user.created_reports.filter(status__in=['new', 'inProgress', 'awaiting', 'done']).count()
        if open_tickets >= 5:
            raise ValidationError("You cannot have more than 5 open tickets.")

    report = form.save(commit=False)
    report.author = user
    report.save()
    return report


def update_report(user, report, form):
    if report.status in ['closed', 'denied']:
        raise ValidationError("Cannot edit closed or denied tickets.")
    if user.role == 'agent':
        form.instance.priority = report.priority

    updated_report = form.save(commit=False)
    updated_report.lastEditDate = timezone.now()
    updated_report.save()
    return updated_report


def take_report(user, report):
    if user.role != 'agent':
        raise ValidationError("Only agents can take tickets.")
    if report.agent:
        raise ValidationError("Ticket is already assigned to an agent.")
    if report.author == user:
        raise ValidationError("You cannot process your own ticket.")

    report.agent = user
    report.status = 'inProgress'
    report.lastEditDate = timezone.now()
    report.save()
    return report


def change_report_status(user, report, new_status, allowed_transitions):
    if new_status not in allowed_transitions:
        raise ValidationError(f"Cannot change status from {report.status} to {new_status}")

    report.status = new_status
    if new_status == 'inProgress' and user.role == 'agent' and not report.agent:
        report.agent = user
    report.lastEditDate = timezone.now()
    report.save()
    return report