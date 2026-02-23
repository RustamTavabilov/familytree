from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Главная и авторизация
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tree/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Мой профиль
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Управление анкетами
    path('profiles/', views.profiles_list, name='profiles_list'),
    path('profiles/create/', views.profile_create, name='profile_create'),
    path('profiles/<int:profile_id>/update/', views.profile_update, name='profile_update'),
    path('profiles/<int:profile_id>/delete/', views.profile_delete, name='profile_delete'),

    # Управление связями
    path('relationships/', views.relationships_list, name='relationships_list'),
    path('relationships/create/', views.relationship_create, name='relationship_create'),
    path('relationships/<int:relationship_id>/delete/', views.relationship_delete, name='relationship_delete'),

    # Визуализация
    path('tree/', views.tree_visualization, name='tree_visualization'),
    path('api/tree-data/', views.get_tree_data, name='tree_data'),
    path('api/tree-data/<int:root_id>/', views.get_tree_data, name='tree_data_root'),
]