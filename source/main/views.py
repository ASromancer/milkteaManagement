import calendar
import json
import sys
import pandas as pd
from _pydecimal import Decimal
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.db.models import F, Sum, ProtectedError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.db.models.functions import ExtractWeek, ExtractMonth
from django.template.loader import get_template, render_to_string
from datetime import date, datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from django.contrib import messages
from django.views.generic import ListView
from django.views.generic.edit import (
    CreateView
)
from .forms import CategoryForm, ProductForm, IngredientForm, RecipeForm, RecipeIngredientForm, \
    SizeForm, ToppingForm, ReceiptForm, RecipeIngredientFormSet, GroupSelectionForm, UserCreationForm, SugarForm, \
    IceForm
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


# Messages
messages_df = pd.read_csv('main/messages.csv')

LOGIN_SUCCESS = messages_df.loc[messages_df['message_key'] == 'LOGIN_SUCCESS', 'message_text'].values[0]
LOGIN_FAIL = messages_df.loc[messages_df['message_key'] == 'LOGIN_FAIL', 'message_text'].values[0]
CREATE_USER_SUCCESS = messages_df.loc[messages_df['message_key'] == 'CREATE_USER_SUCCESS', 'message_text'].values[0]
CREATE_USER_FAIL = messages_df.loc[messages_df['message_key'] == 'CREATE_USER_FAIL', 'message_text'].values[0]
ORDER_SUCCESS = messages_df.loc[messages_df['message_key'] == 'ORDER_SUCCESS', 'message_text'].values[0]
ORDER_ER01 = messages_df.loc[messages_df['message_key'] == 'ORDER_ER01', 'message_text'].values[0]
ORDER_ER02 = messages_df.loc[messages_df['message_key'] == 'ORDER_ER02', 'message_text'].values[0]


# Login
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        messages.success(self.request, LOGIN_SUCCESS)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(self.request, LOGIN_FAIL)
        return super().form_invalid(form)


# Dashboard
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def dashboard(request):
    categories = Category.objects.count()
    products = Product.objects.count()
    ingredients = Ingredient.objects.count()
    expenses = Expense.objects.count()

    context = {
        'categories': categories,
        'products': products,
        'ingredients': ingredients,
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

        # Check if the category has associated products
        if category.product_set.exists():
            return JsonResponse({'status': 'failure', 'message': 'Category has associated products'})

        try:
            category.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Category is associated with protected items'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure', 'message': 'Invalid request method'})


# Products
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_product(request):
    msg = ""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product-list')
        else:
            msg = "Please check the form again."
    form = ProductForm()
    return render(request, 'store/addProduct.html', {'form': form, 'msg': msg})


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

        # Check if the product has associated order items
        if OrderItem.objects.filter(product=product).exists():
            return JsonResponse({'status': 'failure', 'message': 'Product has associated orders'})

        try:
            product.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Product is associated with protected items'})

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

        # Check if the ingredient is used in any recipe
        if RecipeIngredient.objects.filter(ingredient=ingredient).exists():
            return JsonResponse({'status': 'failure', 'message': 'Ingredient is used in recipes'})

        try:
            ingredient.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Ingredient is associated with protected items'})

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

        # Check if the topping is used in any OrderTopping relationship
        if OrderTopping.objects.filter(topping=topping).exists():
            return JsonResponse({'status': 'failure', 'message': 'Topping is used in orders'})

        try:
            topping.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Topping is associated with protected items'})

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


@login_required(login_url='login')
def delete_size(request):
    if request.method == 'POST':
        size_id = request.POST.get('size_id')

        size = get_object_or_404(Size, id=size_id)

        # Check if the size is used in any OrderSize relationship
        if OrderSize.objects.filter(size=size).exists():
            return JsonResponse({'status': 'failure', 'message': 'Size is used in orders'})

        try:
            size.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Size is associated with protected items'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Sugar
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_sugar(request):
    forms = SugarForm()
    if request.method == 'POST':
        forms = SugarForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('sugar-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addSugar.html', context)


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def sugar_list(request):
    sugars = Sugar.objects.all()
    return render(request, 'store/sugar_list.html', {'sugars': sugars})


@csrf_exempt
def update_sugar(request):
    if request.method == 'POST':
        sugar_id = request.POST.get('sugar_id')
        name = request.POST.get('name')

        sugar = get_object_or_404(Sugar, id=sugar_id)
        sugar.name = name

        sugar.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


@login_required(login_url='login')
def delete_sugar(request):
    if request.method == 'POST':
        sugar_id = request.POST.get('sugar_id')

        sugar = get_object_or_404(Sugar, id=sugar_id)

        # Check if the sugar is used in any OrderSugar relationship
        if OrderSugar.objects.filter(sugar=sugar).exists():
            return JsonResponse({'status': 'failure', 'message': 'Sugar type is used in orders'})

        try:
            sugar.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Sugar type is associated with protected items'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


# Ice
@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def create_ice(request):
    forms = IceForm()
    if request.method == 'POST':
        forms = IceForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('ice-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addIce.html', context)


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def ice_list(request):
    ices = Ice.objects.all()
    return render(request, 'store/ice_list.html', {'ices': ices})


@csrf_exempt
def update_ice(request):
    if request.method == 'POST':
        ice_id = request.POST.get('ice_id')
        name = request.POST.get('name')

        ice = get_object_or_404(Ice, id=ice_id)
        ice.name = name

        ice.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})


@login_required(login_url='login')
def delete_ice(request):
    if request.method == 'POST':
        ice_id = request.POST.get('ice_id')

        ice = get_object_or_404(Ice, id=ice_id)

        # Check if the ice type is used in any OrderIce relationship
        if OrderIce.objects.filter(ice=ice).exists():
            return JsonResponse({'status': 'failure', 'message': 'Ice type is used in orders'})

        try:
            ice.delete()
            return JsonResponse({'status': 'success'})
        except ProtectedError:
            return JsonResponse({'status': 'failure', 'message': 'Ice type is associated with protected items'})

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


@login_required(login_url='login')
@user_passes_test(lambda u: not u.groups.filter(name='staff_group').exists(), login_url='pos-page')
def add_receipt(request):
    forms = ReceiptForm()
    if request.method == 'POST':
        forms = ReceiptForm(request.POST)
        if forms.is_valid():
            receipt = forms.save(commit=False)
            selected_ingredient = forms.cleaned_data['ingredient']
            quantity = forms.cleaned_data['quantity']
            ingredient = Ingredient.objects.get(id=selected_ingredient.id)
            receipt.save()
            ingredient.quantity += int(quantity)
            ingredient.save()
            return redirect('receipt-list')
    context = {
        'form': forms
    }
    return render(request, 'store/addReceipt.html', context)


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
    products = Product.objects.filter(recipe__isnull=False)
    toppings = Topping.objects.all()
    sizes = Size.objects.all().order_by('id')
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
    selected_toppings_data = data.get('selectedToppings', '[]')
    selected_toppings = json.loads(selected_toppings_data)

    if not check_ingredients(data):
        resp['status'] = 'failed'
        resp['msg'] = ORDER_ER02
        messages.error(request, ORDER_ER02)
        return HttpResponse(json.dumps(resp), content_type="application/json")

    pref = datetime.now().year + datetime.now().year
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += 1
        check = Order.objects.filter(code=str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        user_id = request.user.id
        sales = Order(user_id=user_id, code=code, sub_total=data['sub_total'], tax=data['tax'],
                      tax_amount=data['tax_amount'],
                      grand_total=data['grand_total'], tendered_amount=data['tendered_amount'],
                      amount_change=data['amount_change'])
        sales.save()
        sale_id = sales.pk
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod
            order_item = OrderItem()
            order_item.order = sales
            product = Product.objects.filter(id=product_id).first()
            qty = int(data.getlist('qty[]')[i])
            price = Decimal(data.getlist('price[]')[i])
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

            i += 1

        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        messages.success(request, ORDER_SUCCESS)

    except Exception as e:
        messages.error(request, ORDER_ER01)
        resp['msg'] = ORDER_ER01

    return HttpResponse(json.dumps(resp), content_type="application/json")


def check_ingredients(data):
    for i, product_id in enumerate(data.getlist('product_id[]')):
        qty = int(data.getlist('qty[]')[i])
        product = Product.objects.filter(id=product_id).first()
        recipe = product.recipe
        recipe_ingredients = recipe.recipeingredient_set.all()

        for recipe_ingredient in recipe_ingredients:
            ingredient = recipe_ingredient.ingredient
            quantity_required = recipe_ingredient.quantity * qty

            if ingredient.quantity < quantity_required:
                return False

    return True


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
def show_report(request):
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
    return render(request, 'store/report.html', context)


@login_required
def get_orders_by_date_range(request):
    if request.method == 'GET':
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        orders = Order.objects.filter(date_added__gte=from_date, date_added__lte=to_date).order_by('date_added')

        total_revenue = orders.aggregate(Sum('grand_total'))['grand_total__sum']

        context = {'orders': orders, 'from_date': from_date, 'to_date': to_date, 'total_revenue': total_revenue}
        html = render_to_string('store/print_orders.html', context)

        return JsonResponse({'html': html})


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
    users = User.objects.filter(is_superuser=False)
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

            messages.success(request, CREATE_USER_SUCCESS)

            return redirect('user-list')
        else:
            messages.error(request, CREATE_USER_FAIL)

    else:
        user_form = UserCreationForm()
        group_form = GroupSelectionForm()

    context = {'user_form': user_form, 'group_form': group_form}
    return render(request, 'store/addUser.html', context)


def active_user(request):
    if request.method == 'POST':
        userId = request.POST.get('user_id')
        userActive = request.POST.get('user_active');
        print(userActive)

        user = get_object_or_404(User, id=userId)
        if userActive == 'True':
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return JsonResponse({'status': 'success'})

    # Return a JSON response indicating failure
    return JsonResponse({'status': 'failure'})
