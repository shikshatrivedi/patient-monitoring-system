from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# Function to handle the root URL
def root_redirect(request):
    return redirect('login')  # Automatically goes to Login page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect),  # <--- This fixes the empty path error
    path('accounts/', include('accounts.urls')),
    path('monitor/', include('monitor.urls')), 
    path('patients/', include('patients.urls')),
     path('accounts/', include('django.contrib.auth.urls')), 
    
    path('', include('monitor.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)