from rest_framework import serializers
from .models import Category, Product, Ingredient, Recipe, RecipeIngredient, Order, OrderItem, OrderTopping, Topping, Size, Receipt


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    recipeingredient_set = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class OrderToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTopping
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    ordertopping_set = OrderToppingSerializer(many=True)

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    orderitem_set = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'


class ToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topping
        fields = '__all__'


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'
