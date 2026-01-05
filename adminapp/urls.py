from django.urls import path
from . import views

urlpatterns = [
    path('owner/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('analytics/', views.admin_analytics, name='admin_analytics'),
    path('audit-log/', views.admin_audit_log, name='admin_audit_log'),
    path('audit-log/delete/<int:id>/', views.audit_log_delete, name='admin_audit_log_delete'),
    path('api/audit-log/<int:id>/', views.audit_log_detail_api, name='api_audit_log_detail'),
    
    # Categories
    path('categories/', views.category_list, name='admin_category_list'),
    path('categories/add/', views.category_add, name='admin_category_add'),
    path('categories/edit/<int:id>/', views.category_edit, name='admin_category_edit'),
    path('categories/delete/<int:id>/', views.category_delete, name='admin_category_delete'),
    
    # Products
    path('products/', views.product_list, name='admin_product_list'),
    path('products/add/', views.product_add, name='admin_product_add'),
    path('products/edit/<int:id>/', views.product_edit, name='admin_product_edit'),
    path('products/delete/<int:id>/', views.product_delete, name='admin_product_delete'),
    
    # Orders
    path('orders/', views.order_list, name='admin_order_list'),
    path('orders/status/<int:id>/<str:status>/', views.order_status_update, name='admin_order_status_update'),
    path('orders/delete/<int:id>/', views.order_delete, name='admin_order_delete'),
    
    # User Management
    path('users/', views.admin_user_list, name='admin_user_list'),
    path('users/delete/<int:id>/', views.admin_user_delete, name='admin_user_delete'),
    
    # Staff Management
    path('admins/', views.admin_list, name='admin_member_list'),
    path('admins/add/', views.admin_add, name='admin_member_add'),
    path('admins/edit/<int:id>/', views.admin_edit, name='admin_member_edit'),
    path('admins/delete/<int:id>/', views.admin_delete, name='admin_member_delete'),

    # API Routes for Details
    path('api/products/<int:id>/', views.product_detail_api, name='api_product_detail'),
    path('api/orders/<int:id>/', views.order_detail_api, name='api_order_detail'),
    path('api/customers/<int:id>/', views.customer_detail_api, name='api_customer_detail'),
    path('api/customers/update/<int:id>/', views.customer_update_api, name='api_customer_update'),
    path('api/categories/<int:id>/', views.category_detail_api, name='api_category_detail'),
]
