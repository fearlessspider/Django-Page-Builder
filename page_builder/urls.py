from django.urls import path
from page_builder.views import PageView

urlpatterns = [
    path('', PageView.as_view(), name='page'),
]