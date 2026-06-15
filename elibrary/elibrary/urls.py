from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from users.views import LoginUserView, register

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('books.urls')),
    path('collections/', include('collection.urls')),

    path('login/', LoginUserView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
