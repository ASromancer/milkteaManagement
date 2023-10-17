from _decimal import Decimal
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.safestring import mark_safe


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="products/", null=True)

    def __str__(self):
        return self.name

    def image_tag(self):
        if self.image:
            return mark_safe('<img src="%s" width="70" />' % (self.image.url))
        else:
            return 'no-image'


class Topping(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Sugar(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Ice(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=100, default='g')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return str(self.product)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, blank=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=100)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tendered_amount = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.FloatField(default=0)
    total = models.FloatField(default=0)


class OrderTopping(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)


class OrderSize(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)


class OrderSugar(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    sugar = models.ForeignKey(Sugar, on_delete=models.CASCADE)


class OrderIce(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    ice = models.ForeignKey(Ice, on_delete=models.CASCADE)


@receiver(post_save, sender=OrderItem)
def update_ingredient_quantity(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        recipe = product.recipe
        recipe_ingredients = recipe.recipeingredient_set.all()

        # Duyệt qua từng RecipeIngredient
        for recipe_ingredient in recipe_ingredients:
            ingredient = recipe_ingredient.ingredient
            quantity = recipe_ingredient.quantity * instance.quantity

            # Giảm số lượng thành phần
            ingredient.quantity -= quantity
            ingredient.save()


class Expense(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, default=None)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient.name} Expense"


@receiver(post_save, sender=OrderItem)
def create_ingredient_expense(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        recipe = product.recipe
        recipe_ingredients = recipe.recipeingredient_set.all()

        for recipe_ingredient in recipe_ingredients:
            if recipe_ingredient.ingredient.quantity < 100:
                Expense.objects.create(ingredient=recipe_ingredient.ingredient)


class Receipt(models.Model):
    supplier = models.CharField(max_length=100)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.quantity * self.price

    def __str__(self):
        return f"Receipt #{self.pk}"


admin_group, _ = Group.objects.get_or_create(name='admin_group')
staff_group, _ = Group.objects.get_or_create(name='staff_group')
