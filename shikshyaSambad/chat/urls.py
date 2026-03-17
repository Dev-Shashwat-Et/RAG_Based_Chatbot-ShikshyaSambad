from django.urls import path
from . import views

urlpatterns = [
    # This means the "empty" path (homepage) points to our chat_home view
    path('', views.chat_home, name='chat_home'),
]
