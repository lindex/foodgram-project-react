from django.contrib import admin
from django.urls import path
from django.urls.conf import include


api = [
    path('', include('users.urls', namespace='users')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api)),
]
