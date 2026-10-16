from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('account:splash')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("account/", include("account.urls")),
    path("archive/", include("archive.urls")),
    path("recommend/", include("recommend.urls")),
    path("discussion/", include("discussion.urls")),
    path("feed/", include("feed.urls")),
    path("", root_redirect, name="root"),
]