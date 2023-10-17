from django import forms
from django.forms import inlineformset_factory, formset_factory
from django.contrib.auth.models import User, Group
from .models import Category, Product, Ingredient, Recipe, RecipeIngredient, Order, OrderItem, OrderTopping, Topping, \
    Size, Receipt, Sugar, Ice


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'})
        }


class ToppingForm(forms.ModelForm):
    class Meta:
        model = Topping
        fields = ['name', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'id': 'price'}),
        }


class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ['name', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'id': 'price'}),
        }


class SugarForm(forms.ModelForm):
    class Meta:
        model = Sugar
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'}),
        }


class IceForm(forms.ModelForm):
    class Meta:
        model = Ice
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'id': 'description'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'category'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'id': 'price'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'image'}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'id': 'unit'}),
        }


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['product']


class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity']


RecipeIngredientFormSet = inlineformset_factory(
    Recipe, RecipeIngredient, form=RecipeIngredientForm,
    extra=1
)


class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['supplier', 'ingredient', 'quantity', 'price']
        widgets = {
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'id': 'supplier'}),
            'ingredient': forms.Select(attrs={'class': 'form-control', 'id': 'ingredient'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'id': 'quantity'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'id': 'price'}),
        }


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Username',
            'password': 'Password',
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'id': 'username'}),
            'password': forms.TextInput(attrs={'class': 'form-control', 'id': 'password'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'first_name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'last_name'}),
        }


class GroupSelectionForm(forms.Form):
    GROUP_CHOICES = (
        ('admin_group', 'Admin Group'),
        ('staff_group', 'Staff Group'),
    )
    group = forms.ChoiceField(widget=forms.RadioSelect, choices=GROUP_CHOICES, required=True, label='Select Group')
