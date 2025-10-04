from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Category, Product, Cart, Order, OrderItem, Review, ChatMessage
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Avg, Q
from django.http import JsonResponse

def home(request):
    categories = Category.objects.all()
    return render(request, 'shopapp/home.html', {'categories': categories})

def category_products(request, category_id):
    category = Category.objects.get(id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'shopapp/products.html', {'products': products, 'category': category})

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, 'Product added to cart successfully!')
    return redirect('cart')

@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shopapp/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            address=request.POST.get('address'),
            phone=request.POST.get('phone')
        )
        
        # Store product IDs for review popup
        product_ids = []
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            product_ids.append(cart_item.product.id)
        
        cart_items.delete()
        
        if payment_method == 'jazzcash':
            messages.success(request, f'Order placed successfully! Payment will be processed through JazzCash ({request.POST.get("jazzcash_number")})')
        else:
            messages.success(request, 'Order placed successfully! You can pay on delivery.')
        
        # Redirect to review page with product IDs
        return redirect(f'/review-products/?order_id={order.id}&products={",".join(map(str, product_ids))}')
    
    return render(request, 'shopapp/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def review_products(request):
    order_id = request.GET.get('order_id')
    product_ids = request.GET.get('products', '').split(',')
    products = Product.objects.filter(id__in=product_ids)
    
    return render(request, 'shopapp/review_products.html', {
        'products': products,
        'order_id': order_id
    })

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shopapp/profile.html', {'orders': orders})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'shopapp/register.html', {'form': form})

@login_required
def add_review(request, product_id):
    product = Product.objects.get(id=product_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Check if user has already reviewed this product
        existing_review = Review.objects.filter(user=request.user, product=product).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
        else:
            # Create new review
            Review.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                comment=comment
            )
        
        messages.success(request, 'Thank you for your review!')
        return redirect('product_detail', product_id=product_id)
    
    return render(request, 'shopapp/add_review.html', {'product': product})

def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    product_images = product.images.all()
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    reviews = product.reviews.all()
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)
    
    # Check if user has purchased the product
    has_purchased = False
    user_has_reviewed = False
    
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user, 
            product=product
        ).exists()
        # Check if user has already reviewed
        user_has_reviewed = Review.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    return render(request, 'shopapp/product_detail.html', {
        'product': product,
        'product_images': product_images,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'has_purchased': has_purchased,
        'user_has_reviewed': user_has_reviewed
    })

def about(request):
    return render(request, 'shopapp/about.html')

def chatbot(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').lower()
        image = request.FILES.get('image')
        location = request.POST.get('location')
        
        # Store chat message
        chat = ChatMessage(
            user=request.user if request.user.is_authenticated else None,
            message=message,
            image=image,
            location=location
        )

        # Basic AI responses
        if 'karachi' in message:
            response = "Here are our stores in Karachi:\n\n1. Dolmen Mall (Clifton)\n   - Location: Dolmen Mall, 3rd Floor, Block 4, Clifton\n   - Phone: +92-333-1234567\n   - <a href='/store/3/' class='store-link'>View Details</a>\n\n2. Ocean Mall (DHA)\n   - Location: Ocean Mall, 2nd Floor, DHA Phase 6\n   - Phone: +92-333-2345678\n   - <a href='/store/4/' class='store-link'>View Details</a>\n\n<a href='/city/karachi/' class='city-link'>View All Karachi Stores</a>"
        elif 'islamabad' in message:
            response = "Here are our stores in Islamabad:\n\n1. Centaurus Mall\n   - Location: Centaurus Mall, 3rd Floor, Jinnah Avenue\n   - Phone: +92-333-7654321\n   - <a href='/store/5/' class='store-link'>View Details</a>\n\n2. Giga Mall\n   - Location: Giga Mall, 2nd Floor, DHA Phase 2\n   - Phone: +92-333-8765432\n   - <a href='/store/6/' class='store-link'>View Details</a>\n\n<a href='/city/islamabad/' class='city-link'>View All Islamabad Stores</a>"
        elif 'lahore' in message:
            response = "Here are our stores in Lahore:\n\n1. Emporium Mall (Johar Town)\n   - Location: Emporium Mall, 2nd Floor, Johar Town\n   - Phone: +92-321-1234567\n   - <a href='/store/1/' class='store-link'>View Details</a>\n\n2. The Forum Mall (Gulberg)\n   - Location: The Forum Mall, 3rd Floor, Gulberg III\n   - Phone: +92-321-2345678\n   - <a href='/store/2/' class='store-link'>View Details</a>\n\n<a href='/city/lahore/' class='city-link'>View All Lahore Stores</a>"
        elif 'hello' in message or 'hi' in message:
            response = "Hello! How can I help you today? 😊"
        elif 'help' in message:
            response = "I'd be happy to help! Are you looking for specific products? Or would you like to know about our services? 🛍️"
        elif 'product' in message:
            response = "Great! I can help you find products. Do you have a specific category in mind? Or would you like to see our popular items? 🔍"
        elif 'location' in message or 'store' in message:
            response = "Please share your city name (Karachi, Lahore, or Islamabad), and I'll help you find the nearest stores! 📍"
        elif image:
            response = "I see you've shared an image! I can help you find similar products. Which city are you located in? 🌆"
        elif location:
            # Get nearby stores based on location
            stores = get_nearby_stores(location)
            response = f"Here are some stores near {location}:\n" + "\n".join(stores)
        else:
            response = "I'm here to help! Feel free to ask about our products, services, or store locations. 😊"

        chat.response = response
        chat.save()

        return JsonResponse({
            'response': response,
            'timestamp': chat.created_at.strftime('%I:%M %p')
        })

    return render(request, 'shopapp/chatbot.html')

def get_nearby_stores(location):
    # This would be replaced with actual store data
    stores = {
        'delhi': [
            'Store 1: Connaught Place - https://maps.google.com/?q=CP+Delhi',
            'Store 2: South Extension - https://maps.google.com/?q=South+Ex+Delhi'
        ],
        'mumbai': [
            'Store 1: Bandra West - https://maps.google.com/?q=Bandra+Mumbai',
            'Store 2: Colaba - https://maps.google.com/?q=Colaba+Mumbai'
        ]
    }
    return stores.get(location.lower(), ['No stores found in this location'])

def store_detail(request, store_id):
    # This view will show store details and map
    return render(request, 'shopapp/store_detail.html', {'store_id': store_id})

def search(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    else:
        products = []
    
    return render(request, 'shopapp/products.html', {
        'products': products,
        'query': query
    })

@login_required
def increase_cart_item(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.increase_quantity()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'quantity': cart_item.quantity,
            'item_total': float(cart_item.get_total())
        })
    return redirect('cart')

@login_required
def decrease_cart_item(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    result = cart_item.decrease_quantity()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if result:
            return JsonResponse({
                'quantity': cart_item.quantity,
                'item_total': float(cart_item.get_total())
            })
        return JsonResponse({'error': 'Cannot decrease quantity below 1'}, status=400)
    return redirect('cart')

@login_required
def remove_cart_item(request, cart_id):
    if request.method == 'POST':
        try:
            cart_item = Cart.objects.get(id=cart_id, user=request.user)
            cart_item.delete()
            return JsonResponse({'success': True})
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart item not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def city_info(request, city):
    # This view will show city-specific store information
    return render(request, 'shopapp/city_info.html', {'city': city.lower()})
