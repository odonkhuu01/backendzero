from django.urls import path
from appbackend import views

urlpatterns = [
    path('user/', views.checkService), # localhost:8000/user/ gehed views.checkService function duudna.
    
]
