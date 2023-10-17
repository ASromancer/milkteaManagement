from django.contrib import admin

from django.contrib import admin
from .models import Category, Product, Ingredient, Recipe, RecipeIngredient, Order, OrderItem, Expense, OrderSize, \
    OrderTopping, Topping, Size, OrderSugar, Sugar, Receipt, OrderIce, Ice


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]


class OrderToppingInline(admin.TabularInline):
    model = OrderTopping


class OrderSizeInline(admin.TabularInline):
    model = OrderSize
    max_num = 1


class OrderSugarInline(admin.TabularInline):
    model = OrderSugar
    max_num = 1


class OrderIceInline(admin.TabularInline):
    model = OrderIce
    max_num = 1


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    inlines = [OrderToppingInline, OrderSizeInline, OrderSugarInline, OrderIceInline]


class OrderItemAdmin(admin.ModelAdmin):
    model = OrderItem
    inlines = [OrderToppingInline, OrderSizeInline, OrderSugarInline, OrderIceInline]


class OrderAdmin(admin.ModelAdmin):
    model = Order
    inlines = [OrderItemInline]


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Topping)
admin.site.register(Sugar)
admin.site.register(Size)
admin.site.register(Ice)
admin.site.register(Ingredient)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Expense)
admin.site.register(Receipt)
