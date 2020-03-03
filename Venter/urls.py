from django.urls import path
from . import views

from Venter.views import OrganisationViewSet, CategoryViewSet, FileViewSet, ModelCPView, ModelWCView, schema_view

urlpatterns = [
    # ex: /venter/organisation
    path('organisation', OrganisationViewSet.as_view({
        'get': 'list'
    })),
    # ex: /venter/category
    path('category', CategoryViewSet.as_view({
        'get': 'list'
    })),
    # ex: /venter/category/XYZ
    path('category/<organisation>', CategoryViewSet.as_view({
        'get': 'retrieve'
    })),
    # ex: /venter/file
    path('file', FileViewSet.as_view({
        'get': 'list'
    })),
    # ex: /venter/file/XYZ
    path('file/<organisation>', FileViewSet.as_view({
        'get': 'retrieve'
    })),
    # ex: /venter/modelCP
    path('modelCP', ModelCPView.as_view()),

    # ex: /venter/modelWC
    path('modelWC', ModelWCView.as_view()),

    path('docs/', schema_view),
]    