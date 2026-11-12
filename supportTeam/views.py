from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone
from datetime import timedelta
from .models import Report, User, Category
from .forms import UserRegisterForm, UserProfileForm, ReportForm, CommentForm, AssignAgentForm
from .selectors import user_selectors, ticket_selectors, comment_selectors, manage_selectors
from .services import ticket_services, comment_services, manage_services, user_services


class SignUpView(CreateView):
    form_class = UserRegisterForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        try:
            user_services.create_user(form)
            return redirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, e.messages[0])
            return self.form_invalid(form)


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(user_selectors.get_user_profile_context(self.request.user))
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        try:
            user_services.update_user_profile(form)
            return redirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, e.messages[0])
            return self.form_invalid(form)


class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10

    def get_queryset(self):
        return ticket_selectors.get_filtered_reports(self.request.user, self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = manage_selectors.get_all_categories()
        context['agents'] = user_selectors.get_agents()
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'

    def get_object(self):
        report = super().get_object()
        user = self.request.user
        if user.role == 'client' and report.author != user:
            raise Http404("You don't have permission to view this.")
        if user.role == 'agent' and report.agent != user and report.status != 'new':
            raise Http404("You don't have permission to view this.")
        return report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        report = self.get_object()

        context['comments'] = comment_selectors.get_comments_for_report(user, report)
        context['comment_form'] = CommentForm()
        context['allowed_transitions'] = ticket_selectors.get_allowed_transitions(user, report)
        context['can_assign'] = user.role == 'manager'
        context['can_take'] = user.role == 'agent' and report.status == 'new' and report.author != user

        # Fix can_edit: Do not show Edit button if status is done, closed or denied
        context['can_edit'] = (user.role == 'manager' or (
                    user.role == 'client' and report.author == user)) and report.status not in ['done', 'closed',
                                                                                                'denied']

        # Add specific check for the Reopen button
        context['can_reopen'] = (
                user.role == 'client' and
                report.status == 'done' and
                (timezone.now() - report.lastEditDate <= timedelta(days=3))
        )

        return context


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/report_form.html'
    success_url = reverse_lazy('report_list')

    def form_valid(self, form):
        try:
            ticket_services.create_report(self.request.user, form)
            return redirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, e.messages[0])
            return self.form_invalid(form)


class ReportUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/report_form.html'
    success_url = reverse_lazy('report_list')

    def test_func(self):
        report = self.get_object()
        user = self.request.user
        if report.status in ['closed', 'denied', 'done']:
            return False
        if user.role == 'manager':
            return True
        if user.role == 'client' and report.author == user:
            return True
        return False

    def form_valid(self, form):
        try:
            ticket_services.update_report(self.request.user, self.get_object(), form)
            return redirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, e.messages[0])
            return self.form_invalid(form)


class TakeTicketView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        try:
            ticket_services.take_report(request.user, report)
            messages.success(request, "Ticket taken.")
        except ValidationError as e:
            messages.error(request, e.messages[0])
        return redirect('report_detail', pk=pk)


class ChangeStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)

        if request.user.role == 'client' and report.author != request.user:
            raise Http404("You do not have permission to modify this ticket.")

        new_status = request.POST.get('status')
        allowed = ticket_selectors.get_allowed_transitions(request.user, report)

        try:
            ticket_services.change_report_status(request.user, report, new_status, allowed)
            messages.success(request, "Status updated.")
        except ValidationError as e:
            messages.error(request, e.messages[0])

        return redirect('report_detail', pk=pk)


class AssignAgentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Report
    form_class = AssignAgentForm
    template_name = 'reports/assign_agent.html'
    success_url = reverse_lazy('report_list')

    def test_func(self):
        return self.request.user.role == 'manager'


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)

        if request.user.role == 'client' and report.author != request.user:
            raise Http404("You do not have permission to comment on this ticket.")

        form = CommentForm(request.POST)
        if form.is_valid():
            try:
                comment_services.add_comment(request.user, report, form)
                messages.success(request, "Comment added.")
            except ValidationError as e:
                messages.error(request, e.messages[0])
        return redirect('report_detail', pk=pk)


class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'

    def test_func(self):
        return self.request.user.role == 'manager'

    def get_queryset(self):
        return manage_selectors.get_all_categories()


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Category
    fields = ['name']
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.role == 'manager'

    def form_valid(self, form):
        try:
            manage_services.save_category(self.request.user, form)
            return redirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, e.messages[0])
            return self.form_invalid(form)


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    fields = ['name']
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.role == 'manager'

    def form_valid(self, form):
        try:
            manage_services.save_category(self.request.user, form)
            return redirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, e.messages[0])
            return self.form_invalid(form)


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.role == 'manager'

    def delete(self, request, *args, **kwargs):
        try:
            manage_services.delete_category(request.user, self.get_object())
            return redirect(self.success_url)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect(self.success_url)