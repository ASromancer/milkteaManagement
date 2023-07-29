import calendar
import json
import sys
from _pydecimal import Decimal

from django.contrib.auth.models import Group, User
from django.db.models import F, Sum

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.db.models.functions import ExtractWeek, ExtractMonth
from django.utils import timezone
from rest_framework import viewsets
from datetime import date, datetime, timedelta

from .serializers import CategorySerializer, ProductSerializer, IngredientSerializer, RecipeSerializer, \
    RecipeIngredientSerializer, OrderSerializer, OrderItemSerializer, OrderToppingSerializer, ToppingSerializer, \
    SizeSerializer, ReceiptSerializer
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from django.contrib import messages
from django.views.generic import ListView
from django.views.generic.edit import (
    CreateView
)
from .forms import CategoryForm, ProductForm, IngredientForm, RecipeForm, RecipeIngredientForm, \
    SizeForm, ToppingForm, ReceiptForm, RecipeIngredientFormSet, GroupSelectionForm, UserCreationForm
from .models import Category, Product, Ingredient, Recipe, Order, OrderItem, Expense, RecipeIngredient, OrderTopping, \
    Topping, Size, Receipt, OrderSize, OrderSugar, Sugar, Ice, OrderIce


# Access modifiers
def can_access_pos(user):
    return user.groups.filter(name='staff_group').exists()


# Report
def get_monthly_revenue():
    monthly_revenue_data = Order.objects.annotate(month=ExtractMonth('date_created')).values('month').annotate(
        revenue=Sum('grand_total')).order_by('month')
    data = [{'month': item['month'], 'revenue': item['revenue']} for item in monthly_revenue_data]
    return data


# Function to calculate weekly revenue
def get_weekly_revenue():
    weekly_revenue_data = Order.objects.annotate(week=ExtractWeek('date_created')).values('week').annotate(
        revenue=Sum('grand_total')).order_by('week')
    data = [{'week': item['week'], 'revenue': item['revenue']} for item in weekly_revenue_data]
    return data


# Function to calculate revenue by product
def get_product_revenue():
    product_revenue_data = OrderItem.objects.values('product__name').annotate(revenue=Sum('total')).order_by(
        'product__name')
    data = [{'product': item['product__name'], 'revenue': item['revenue']} for item in product_revenue_data]
    return data


# Function to calculate revenue by category
def get_category_revenue():
    category_revenue_data = OrderItem.objects.values('product__category__name').annotate(revenue=Sum('total')).order_by(
        'product__category__name')
    data = [{'category': item['product__category__name'], 'revenue': item['revenue']} for item in category_revenue_data]
    return data


# Function to calculate expense by month
def get_receipt_expenses_by_month():
    expenses_by_month = Receipt.objects.annotate(total_expenses=F('price') * F('quantity')).values(
        'date_created__month').annotate(total_expenses_sum=Sum('total_expenses')).order_by('date_created__month')

    data = [{'month': item['date_created__month'], 'total_expenses': item['total_expenses_sum']} for item in
            expenses_by_month]

    return data


# Views for JSON response
def get_monthly_revenue_data(request):
    monthly_revenue_data = get_monthly_revenue()
    return JsonResponse(monthly_revenue_data, safe=False)


def get_weekly_revenue_data(request):
    weekly_revenue_data = get_weekly_revenue()
    return JsonResponse(weekly_revenue_data, safe=False)


def get_product_revenue_data(request):
    product_revenue_data = get_product_revenue()
    return JsonResponse(product_revenue_data, safe=False)


def get_category_revenue_data(request):
    category_revenue_data = get_category_revenue()
    return JsonResponse(category_revenue_data, safe=False)


def get_receipt_expenses_by_month_data(request):
    monthly_expenses_data = get_receipt_expenses_by_month()
    return JsonResponse(monthly_expenses_data, safe=False)


# Dashboard
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def dashboard(request):
    # Thống kê các số liệu liên quan
    categories = Category.objects.count()
    products = Product.objects.count()
    ingredients = Ingredient.objects.count()
    recipes = Recipe.objects.count()
    order_items = OrderItem.objects.count()
    expenses = Expense.objects.count()

    # Gọi hàm revenue_statistics để lấy thông tin doanh thu

    # Truyền dữ liệu vào context
    context = {
        'categories': categories,
        'products': products,
        'ingredients': ingredients,
        'recipes': recipes,
        'order_items': order_items,
        'expenses': expenses,
    }

    return render(request, 'base/dashboard.html', context)


# Categories
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_category(request):
    forms = CategoryForm()
    if request.method == 'POST':
        forms = CategoryForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('category-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addCategory.html', context)


class CategoryListView(ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'category'


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def update_category(request):
    if request.method == 'POST':
        categoryId = request.POST.get('category_id')
        new_name = request.POST.get('new_name')

        category = get_object_or_404(Category, id=categoryId)
        category.name = new_name
        category.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def delete_category(request):
    if request.method == 'POST':
        categoryId = request.POST.get('category_id')

        category = get_object_or_404(Category, id=categoryId)
        category.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Products
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
        return redirect('product-list')
    form = ProductForm()
    return render(request, 'store/addProduct.html', {'form': form})


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {'product': products, 'categories': categories})


@csrf_exempt
def update_product(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        price = request.POST.get('price')

        product = get_object_or_404(Product, id=product_id)
        product.name = name
        product.description = description
        product.category_id = category_id
        product.price = price

        if 'new_image' in request.FILES:
            product.image = request.FILES['new_image']

        product.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


def delete_product(request):
    if request.method == 'POST':
        productId = request.POST.get('product_id')

        product = get_object_or_404(Product, id=productId)
        product.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Ingredients
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_ingredient(request):
    forms = IngredientForm()
    if request.method == 'POST':
        forms = IngredientForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('ingredient-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addIngredient.html', context)


class IngredientListView(ListView):
    model = Ingredient
    template_name = 'store/ingredient_list.html'
    context_object_name = 'ingredient'


@csrf_exempt
def update_ingredient(request):
    if request.method == 'POST':
        ingredient_id = request.POST.get('ingredient_id')
        name = request.POST.get('name')
        quantity = request.POST.get('quantity')
        unit = request.POST.get('unit')

        ingredient = get_object_or_404(Ingredient, id=ingredient_id)
        ingredient.name = name
        ingredient.quantity = quantity
        ingredient.unit = unit

        ingredient.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


def delete_ingredient(request):
    if request.method == 'POST':
        ingredientId = request.POST.get('ingredient_id')

        ingredient = get_object_or_404(Ingredient, id=ingredientId)
        ingredient.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Toppings
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_topping(request):
    forms = ToppingForm()
    if request.method == 'POST':
        forms = ToppingForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('topping-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addTopping.html', context)


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def topping_list(request):
    toppings = Topping.objects.all()
    return render(request, 'store/topping_list.html', {'toppings': toppings})


@csrf_exempt
def update_topping(request):
    if request.method == 'POST':
        topping_id = request.POST.get('topping_id')
        name = request.POST.get('name')
        price = request.POST.get('price')

        topping = get_object_or_404(Topping, id=topping_id)
        topping.name = name
        topping.price = price

        topping.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


def delete_topping(request):
    if request.method == 'POST':
        topping_id = request.POST.get('topping_id')

        topping = get_object_or_404(Topping, id=topping_id)
        topping.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Sizes
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_size(request):
    forms = SizeForm()
    if request.method == 'POST':
        forms = SizeForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('size-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addSize.html', context)


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def size_list(request):
    sizes = Size.objects.all()
    return render(request, 'store/size_list.html', {'sizes': sizes})


@csrf_exempt
def update_size(request):
    if request.method == 'POST':
        size_id = request.POST.get('size_id')
        name = request.POST.get('name')
        price = request.POST.get('price')

        size = get_object_or_404(Size, id=size_id)
        size.name = name
        size.price = price

        size.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


def delete_size(request):
    if request.method == 'POST':
        size_id = request.POST.get('size_id')

        size = get_object_or_404(Size, id=size_id)
        size.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Recipes
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_recipe(request):
    error_message = ""
    if request.method == 'POST':
        # Save the recipe when the form is submitted
        selected_product_id = request.POST.get('product')

        # Check if a product is selected
        if selected_product_id:
            selected_ingredient_ids = request.POST.getlist('ingredient')
            quantities = request.POST.getlist('quantity')
            quantities = [qty for qty in quantities if qty.strip()]
            print(selected_ingredient_ids)
            print(quantities)

            product = Product.objects.get(pk=selected_product_id)
            recipe = Recipe.objects.create(product=product)

            for ingredient_id, quantity in zip(selected_ingredient_ids, quantities):
                ingredient = Ingredient.objects.get(pk=ingredient_id)
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity=quantity)

            return redirect('recipe-list')  # Redirect after successful save
        else:
            # Return the template with an error message or any relevant information
            error_message = "All products have recipes."
            all_products = Product.objects.all()

            # Get the primary keys of products that have a recipe
            products_with_recipe_pks = Recipe.objects.values_list('product', flat=True)

            # Find products without a recipe
            products_without_recipe = all_products.exclude(pk__in=products_with_recipe_pks)
            ingredients = Ingredient.objects.all()
            context = {'products': products_without_recipe, 'ingredients': ingredients, 'error_message': error_message}
            return render(request, 'store/addRecipe.html', context)

    # Display the recipe form
    all_products = Product.objects.all()

    # Get the primary keys of products that have a recipe
    products_with_recipe_pks = Recipe.objects.values_list('product', flat=True)

    # Find products without a recipe
    products_without_recipe = all_products.exclude(pk__in=products_with_recipe_pks)
    ingredients = Ingredient.objects.all()
    context = {'products': products_without_recipe, 'ingredients': ingredients, 'error_message': error_message}
    return render(request, 'store/addRecipe.html', context)


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def product_recipe_ingredients(request, product_id):
    product = Product.objects.get(id=product_id)
    recipe = Recipe.objects.get(product=product)
    recipe_ingredient = RecipeIngredient.objects.filter(recipe=recipe)
    return render(request, 'store/recipe_detail.html', {'product': product, 'recipe_ingredient': recipe_ingredient})


@csrf_exempt
def update_recipe_ingredient(request):
    if request.method == 'POST':
        recipeIngredientId = request.POST.get('recipe_ingredient_id')

        recipeIngredient = get_object_or_404(RecipeIngredient, id=recipeIngredientId)

        recipeIngredient.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


def delete_recipe_ingredient(request):
    if request.method == 'POST':
        recipeIngredientId = request.POST.get('recipe_ingredient_id')

        recipeIngredient = get_object_or_404(RecipeIngredient, id=recipeIngredientId)
        recipeIngredient.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


def delete_recipe(request):
    if request.method == 'POST':
        recipeId = request.POST.get('recipe_id')

        recipe = get_object_or_404(Recipe, product_id=recipeId)
        recipe.delete()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


class RecipeListView(ListView):
    model = Recipe
    template_name = 'store/recipe_list.html'
    context_object_name = 'recipe'


# Expense
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def expense_list(request):
    expenses = Expense.objects.all()
    ingredients = Ingredient.objects.all()
    return render(request, 'store/expense_list.html', {'expenses': expenses, 'ingredients': ingredients})


# Receipts
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def receipt_list(request):
    receipts = Receipt.objects.all()
    return render(request, 'store/receipt_list.html', {'receipts': receipts})


@csrf_exempt
def create_receipt(request):
    if request.method == 'POST':
        ingredient_id = request.POST.get('ingredient_id')
        supplier = request.POST.get('supplier')
        quantity = request.POST.get('quantity')
        price = request.POST.get('price')
        expense_id = request.POST.get('expense_id')
        expense = Expense.objects.get(id=expense_id)

        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return JsonResponse({'status': 'error'})

        receipt = Receipt.objects.create(
            supplier=supplier,
            ingredient=ingredient,
            quantity=quantity,
            price=price
        )

        receipt.save()
        # Increase the ingredient quantity
        ingredient.quantity += int(quantity)
        ingredient.save()
        if ingredient.quantity > 100:
            expense.delete()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})


# POS
@login_required
def pos(request):
    products = Product.objects.all()
    toppings = Topping.objects.all()
    sizes = Size.objects.all().order_by('-id')
    sugars = Sugar.objects.all()
    ices = Ice.objects.all()
    product_json = []
    for product in products:
        product_json.append({'id': product.id, 'name': product.name, 'price': float(product.price)})
    context = {
        'page_title': "Point of Sale",
        'products': products,
        'toppings': toppings,
        'sizes': sizes,
        'sugars': sugars,
        'ices': ices,
        'product_json': json.dumps(product_json)
    }
    return render(request, 'POS/pos.html', context)


@login_required
def checkout_modal(request):
    grand_total = 0
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total': grand_total,
    }
    return render(request, 'POS/checkout.html', context)


@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    print(data)
    selected_toppings_data = data.get('selectedToppings', '[]')
    selected_toppings = json.loads(selected_toppings_data)

    pref = datetime.now().year + datetime.now().year
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = Order.objects.filter(code=str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        user_id = request.user.id
        sales = Order(user_id=user_id, code=code, sub_total=data['sub_total'], tax=data['tax'], tax_amount=data['tax_amount'],
                      grand_total=data['grand_total'], tendered_amount=data['tendered_amount'],
                      amount_change=data['amount_change'])
        sales.save()
        sale_id = sales.pk
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod
            order_item = OrderItem()
            order_item.order = sales  # Set the 'order' field to the related Order
            product = Product.objects.filter(id=product_id).first()
            qty = int(data.getlist('qty[]')[i])
            price = Decimal(data.getlist('price[]')[i])  # Convert to Decimal
            order_item.product = product
            order_item.quantity = qty
            order_item.price = price
            total = Decimal(data.getlist('total[]')[i])
            order_item.total = total
            order_item.save()

            toppings_for_product = selected_toppings[i]
            if toppings_for_product:
                for topping_id in toppings_for_product:
                    topping = Topping.objects.filter(id=int(topping_id)).first()
                    OrderTopping.objects.create(order_item=order_item, topping=topping)

            all_keys = data.keys()

            size_keys = [key for key in all_keys if key.startswith('order_item_size_')]
            sugar_keys = [key for key in all_keys if key.startswith('order_item_sugar_')]
            ice_keys = [key for key in all_keys if key.startswith('order_item_ice_')]

            size_id = int(data.get(size_keys[i], 0))
            sugar_id = int(data.get(sugar_keys[i], 0))
            ice_id = int(data.get(ice_keys[i], 0))

            if size_id > 0:
                size = Size.objects.filter(id=size_id).first()
                OrderSize.objects.create(order_item=order_item, size=size)

            if sugar_id > 0:
                sugar = Sugar.objects.filter(id=sugar_id).first()
                OrderSugar.objects.create(order_item=order_item, sugar=sugar)

            if ice_id > 0:
                ice = Ice.objects.filter(id=ice_id).first()
                OrderIce.objects.create(order_item=order_item, ice=ice)

            i += int(1)

        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        messages.success(request, "Sale Record has been saved.")
    except Exception as e:
        resp['msg'] = "An error occurred"
        print("Unexpected error:", sys.exc_info()[0])
        print("Exception details:", e)
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def salesList(request):
    sales = Order.objects.all()
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale, field.name)
        data['items'] = OrderItem.objects.filter(order=sale).all()
        data['item_count'] = len(data['items'])
        if 'tax_amount' in data:
            data['tax_amount'] = format(float(data['tax_amount']), '.2f')
        sale_data.append(data)
    context = {
        'page_title': 'Sales Transactions',
        'sale_data': sale_data,
    }
    return render(request, 'POS/sales.html', context)


@login_required
def receipt(request):
    id = request.GET.get('id')
    sales = Order.objects.filter(id=id).first()
    transaction = {}
    for field in Order._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)
    if 'tax_amount' in transaction:
        transaction['tax_amount'] = format(float(transaction['tax_amount']), '.2f')

    # Use Prefetch to fetch toppings, sizes, and sugar for each order item
    order_items = OrderItem.objects.filter(order=sales).prefetch_related(
        Prefetch('ordertopping_set', queryset=OrderTopping.objects.select_related('topping')),
        Prefetch('ordersize_set', queryset=OrderSize.objects.select_related('size')),
        Prefetch('ordersugar_set', queryset=OrderSugar.objects.select_related('sugar')),
        Prefetch('orderice_set', queryset=OrderIce.objects.select_related('ice')),
    )

    context = {
        "transaction": transaction,
        "salesItems": order_items
    }
    return render(request, 'POS/receipt.html', context)


# User
@login_required
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def user_list(request):
    users = User.objects.all()
    return render(request, 'store/user_list.html', {'users': users})


@login_required
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_user(request):
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        group_form = GroupSelectionForm(request.POST)

        if user_form.is_valid() and group_form.is_valid():
            user = user_form.save(commit=False)
            password = user_form.cleaned_data['password']
            user.set_password(password)
            user.save()

            group_name = group_form.cleaned_data['group']
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

            return redirect('user-list')  # Redirect to user list page after successful save
    else:
        user_form = UserCreationForm()
        group_form = GroupSelectionForm()

    context = {'user_form': user_form, 'group_form': group_form}
    return render(request, 'store/addUser.html', context)


################################
# DRF
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class ToppingViewSet(viewsets.ModelViewSet):
    queryset = Topping.objects.all()
    serializer_class = ToppingSerializer


class SizeViewSet(viewsets.ModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer


class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer


class OrderToppingViewSet(viewsets.ModelViewSet):
    queryset = OrderTopping.objects.all()
    serializer_class = OrderToppingSerializer
