def get_comments_for_report(user, report):
    comments = report.comments.all()
    if user.role == 'client':
        comments = comments.filter(secret=False)
    return comments