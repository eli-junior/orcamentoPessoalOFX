"""URLs do core do orçamento."""

from django.contrib.auth import views as auth_views
from django.urls import path

from orcamento_2026.core import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),
    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    # Autenticação
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="core/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    # Categorias
    path("categorias/", views.CategoryListView.as_view(), name="category_list"),
    path("categorias/nova/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categorias/<int:pk>/editar/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categorias/<int:pk>/excluir/", views.CategoryDeleteView.as_view(), name="category_delete"),
    # Subcategorias
    path("subcategorias/", views.SubCategoryListView.as_view(), name="subcategory_list"),
    path("subcategorias/nova/", views.SubCategoryCreateView.as_view(), name="subcategory_create"),
    path("subcategorias/<int:pk>/editar/", views.SubCategoryUpdateView.as_view(), name="subcategory_update"),
    path("subcategorias/<int:pk>/excluir/", views.SubCategoryDeleteView.as_view(), name="subcategory_delete"),
    # Despesas
    path("despesas/", views.ExpenseListView.as_view(), name="expense_list"),
    path("despesas/nova/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("despesas/<int:pk>/editar/", views.ExpenseUpdateView.as_view(), name="expense_update"),
    path("despesas/<int:pk>/excluir/", views.ExpenseDeleteView.as_view(), name="expense_delete"),
    # Transações
    path("transacoes/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transacoes/<int:pk>/consolidar/", views.transaction_consolidate, name="transaction_consolidate"),
    # Sugestões (Larry)
    path("sugestoes/", views.suggestion_list, name="suggestion_list"),
    path("sugestoes/gerar/", views.suggestion_generate, name="suggestion_generate"),
    path("sugestoes/<int:pk>/aceitar/", views.suggestion_accept, name="suggestion_accept"),
    path("sugestoes/<int:pk>/rejeitar/", views.suggestion_reject, name="suggestion_reject"),
    path("api/pending-suggestions-count/", views.pending_suggestions_count, name="pending_suggestions_count"),
    # Importação
    path("importar/", views.import_ofx_view, name="import_ofx"),
    # API HTMX
    path("api/subcategories/", views.get_subcategories_by_category, name="api_subcategories"),
]
