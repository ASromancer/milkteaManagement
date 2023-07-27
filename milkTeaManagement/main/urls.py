from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from rest_framework import routers, permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from .views import CategoryViewSet, ProductViewSet, IngredientViewSet, RecipeViewSet, RecipeIngredientViewSet, \
    OrderViewSet, OrderItemViewSet, OrderToppingViewSet, ToppingViewSet, SizeViewSet, ReceiptViewSet
from .views import dashboard, CategoryListView, create_category, create_product, IngredientListView, \
    create_ingredient, RecipeListView, product_recipe_ingredients, \
    update_category, delete_category, update_product, delete_product, product_list, update_ingredient, \
    delete_ingredient, delete_recipe, delete_recipe_ingredient, update_recipe_ingredient, topping_list, \
    create_topping, size_list, create_size, update_topping, delete_topping, update_size, delete_size, expense_list, \
    create_receipt, receipt_list, create_recipe, pos, receipt, salesList, save_pos, checkout_modal, \
    get_category_revenue_data, get_product_revenue_data, get_weekly_revenue_data, get_monthly_revenue_data, \
    get_receipt_expenses_by_month_data, create_user, user_list

router = routers.DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'recipe-ingredients', RecipeIngredientViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'order-toppings', OrderToppingViewSet)
router.register(r'toppings', ToppingViewSet)
router.register(r'sizes', SizeViewSet)
router.register(r'receipts', ReceiptViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="MilkTea Management API",
        default_version="v1",
        contact=openapi.Contact(email="nguyentuanhiep01@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API
    path('api/', include(router.urls)),
    path('', dashboard, name='dashboard'),

    # App
    path('category-list/', CategoryListView.as_view(), name='category-list'),
    path('create-category/', create_category, name='create-category'),
    path('update-category/', update_category, name='update-category'),
    path('delete-category/', delete_category, name='delete-category'),

    path('product-list/', product_list, name='product-list'),
    path('create-product/', create_product, name='create-product'),
    path('update-product/', update_product, name='update-product'),
    path('delete-product/', delete_product, name='delete-product'),

    path('topping-list/', topping_list, name='topping-list'),
    path('create-topping/', create_topping, name='create-topping'),
    path('update-topping/', update_topping, name='update-topping'),
    path('delete-topping/', delete_topping, name='delete-topping'),

    path('size-list/', size_list, name='size-list'),
    path('create-size/', create_size, name='create-size'),
    path('update-size/', update_size, name='update-size'),
    path('delete-size/', delete_size, name='delete-size'),

    path('ingredient-list/', IngredientListView.as_view(), name='ingredient-list'),
    path('create-ingredient/', create_ingredient, name='create-ingredient'),
    path('update-ingredient/', update_ingredient, name='update-ingredient'),
    path('delete-ingredient/', delete_ingredient, name='delete-ingredient'),

    path('recipe-list/', RecipeListView.as_view(), name='recipe-list'),
    path('recipe-list/<product_id>', product_recipe_ingredients, name='recipe-list'),
    path('create-recipe/', create_recipe, name='create-recipe'),
    path('delete-recipe/', delete_recipe, name='delete-recipe'),
    path('update-recipe-ingredient/', update_recipe_ingredient, name='delete-recipe'),
    path('delete-recipe-ingredient/', delete_recipe_ingredient, name='delete-recipe'),

    # path('order-list/', OrderListView.as_view(), name='order-list'),
    # path('order-item/<order_id>', order_item, name='order-item'),

    path('expense-list/', expense_list, name='expense-list'),

    path('receipt-list/', receipt_list, name='receipt-list'),
    path('create-receipt/', create_receipt, name='create-receipt'),

    # POS
    path('pos', pos, name="pos-page"),
    path('checkout-modal', checkout_modal, name="checkout-modal"),
    path('save-pos', save_pos, name="save-pos"),
    path('sales', salesList, name="sales-page"),
    path('receipt', receipt, name="receipt-modal"),

    # Report
    path('get_monthly_revenue_data/', get_monthly_revenue_data, name='get_monthly_revenue_data'),
    path('get_weekly_revenue_data/', get_weekly_revenue_data, name='get_weekly_revenue_data'),
    path('get_product_revenue_data/', get_product_revenue_data, name='get_product_revenue_data'),
    path('get_category_revenue_data/', get_category_revenue_data, name='get_category_revenue_data'),
    path('get_receipt_expenses_by_month_data/', get_receipt_expenses_by_month_data, name='get_receipt_expenses_by_month_data'),

    # User
    path('create-user/', create_user, name='create-user'),
    path('user-list/', user_list, name='user-list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
