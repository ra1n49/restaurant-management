from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.Home, name='home'),
    
    path("", views.custom_login, name="custom_login"),
    path('logout', views.logout_user, name='logout'),
    
    path('ban/', views.ban_view, name='ban_view'),
    path('ban/search/', views.search_ban_view, name='search_ban_view'),
    path('ban/add/', views.add_ban, name='add_ban'),
    path('ban/edit/<int:ban_id>/', views.edit_ban, name='edit_ban'),
    path('ban/delete/<int:ban_id>/', views.delete_ban, name='delete_ban'),
    
    path('ban/<int:ban_id>/order_detail/', views.order_detail_view, name='order_detail'),
    path('ban/order_detail/<int:order_id>/update/', views.update_order_customer, name='update_order_customer'),
    path('ban/order_detail/<int:order_id>/thanh_toan/', views.thanh_toan, name='thanh_toan'),
    path('update-tinhtrang/<int:chi_tiet_order_id>/', views.update_tinhtrang, name='update_tinhtrang'),
    
    path('employees/', views.all_employees, name='all_employees'),
    path('employees/search/', views.search_nhanvien_view, name='search_nhanvien_view'),
    path("employees/add/", views.add_employee, name="add_employee"),
    path("employees/edit/<int:pk>/", views.edit_employee, name="edit_employee"),
    path("employees/delete/<int:pk>/", views.delete_employee, name="delete_employee"),
    path('employees/<int:employee_id>/shifts/', views.calamviec_nv, name='calamviec_nv'),
   
    path('menu/', views.menu_view, name='menu'),
    path('menu/search/', views.search_menu_view, name='search_menu_view'),
    path('menu/add/', views.add_menu_view, name='add_menu_view'),  
    path('menu/edit/<int:menu_id>/', views.edit_menu_view, name='edit_menu_view'),  
    path('menu/delete/<int:menu_id>/', views.delete_menu_view, name='delete_menu_view'), 
    
    path('doanhthu', views.order_view, name='order_view'),
    path('doanhthu/search/', views.search_order_detail_dapaid, name='search_order_detail_dapaid'),
    path('doanhthu/<int:order_id>/', views.order_detail_dapaid, name='order_detail_dapaid'),
    
    path('calamviec/', views.calamviec, name='calamviec'),
    path('calamviec/them-ca-lam-viec/', views.them_ca_lam_viec, name='them_ca_lam_viec'),
    path('calamviec/sua-ca-lam-viec/<int:pk>/', views.sua_ca_lam_viec, name='sua_ca_lam_viec'),
    path('calamviec/xoa-ca-lam-viec/<int:pk>/', views.xoa_ca_lam_viec, name='xoa_ca_lam_viec'),
    path('calamviec/cham-cong-vao/<int:id>/', views.cham_cong_vao, name='cham_cong_vao'),
    path('calamviec/cham-cong-ra/<int:id>/', views.cham_cong_ra, name='cham_cong_ra'),
    path('calamviec/nhanvientrongca/', views.nhanvientrongca, name='nhanvientrongca'),

]
