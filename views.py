from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

@login_required
@csrf_protect
def add_product(request):
    if request.method == 'POST':
        # Your product adding logic here
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    
    context = {'form': form}
    return render(request, 'admin/product_add.html', context) 