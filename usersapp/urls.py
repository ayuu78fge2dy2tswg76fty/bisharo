from django.urls import path
from .views import home_v, profile_v,  logout_v, edit_profile_v

urlpatterns = [
    # path('homeuser/', users_v, name='user_login'),
    # path('register/', register_v, name='user_register'),
    path('logout/', logout_v, name='user_logout'),
    path('home/', home_v, name='user_home'),
    path('profile/', profile_v, name='user_profile'),
    path('profile/edit/', edit_profile_v, name='edit_profile'),
]
