from django.core.exceptions import ValidationError


def add_comment(user, report, form):
    if report.status in ['closed', 'denied']:
        raise ValidationError("Cannot comment on closed or denied tickets.")
    if user.role == 'client' and report.author != user:
        raise ValidationError("You can only comment on your own tickets.")
    if user.role == 'agent' and report.agent != user:
        raise ValidationError("You can only comment on assigned tickets.")

    comment = form.save(commit=False)
    comment.author = user
    comment.report = report

    if user.role == 'client':
        comment.secret = False

    comment.save()
    return comment