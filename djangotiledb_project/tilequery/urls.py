from django.urls import path
from . import views

urlpatterns = [
    path('vcf-query-api/', views.TileDBVCFQueryView.as_view(), name='vcf-query'),
    path('', views.index, name='index'),
]
