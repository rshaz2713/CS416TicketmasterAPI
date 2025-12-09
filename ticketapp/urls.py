from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('save_favorite/', views.save_favorite, name='save_favorite'),
    path('remove_favorite', views.remove_favorite, name='remove_favorite'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/<int:id>/edit/', views.edit_favorite, name='edit_favorite'),
]
