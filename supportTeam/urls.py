from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report_list'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/update/', views.ReportUpdateView.as_view(), name='report_update'),
    path('reports/<int:pk>/take/', views.TakeTicketView.as_view(), name='take_ticket'),
    path('reports/<int:pk>/status/', views.ChangeStatusView.as_view(), name='change_status'),
    path('reports/<int:pk>/assign/', views.AssignAgentView.as_view(), name='assign_agent'),
    path('reports/<int:pk>/comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]