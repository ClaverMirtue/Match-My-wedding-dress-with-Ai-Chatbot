from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-review/<int:product_id>/', views.add_review, name='add_review'),
    path('review-products/', views.review_products, name='review_products'),
    path('about/', views.about, name='about'),
    path('store/<int:store_id>/', views.store_detail, name='store_detail'),
    path('search/', views.search, name='search'),
    path('login/', auth_views.LoginView.as_view(
        template_name='shopapp/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='shopapp/home.html',
        next_page='home'
    ), name='logout'),
    path('cart/increase/<int:cart_id>/', views.increase_cart_item, name='increase_cart_item'),
    path('cart/decrease/<int:cart_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('cart/remove/<int:cart_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('city/<str:city>/', views.city_info, name='city_info'),
] 