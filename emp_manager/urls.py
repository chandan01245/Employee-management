"""
URL configuration for Assignment project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("",views.login_page,name='login'),
    path("Dashboard/",views.dashboard_page,name="dashboard"),
    path("EmployeeList/",views.employee_list,name="employee_list"),
    path("CreateEmployee/",views.create_employee,name="new_employee"),
    path("UpdateEmployee/<employee_id>",views.edit_employee,name="change_employee"),
    path("Delete_employee/<employee_id>",views.delete_employee,name="delete_employee"),
    path('image/<int:employee_id>/', views.serve_image, name='serve_image'),
    path('check-email/', views.check_email_duplicate, name='check_email_duplicate'),
    path("",views.logout_page,name="logout"),
]
