import logging
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from orcamento_2026.core.models import Expense, Category
from decouple import config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run Telegram Bot"

    def handle(self, *args, **kwargs):
        token = config("TELEGRAM_TOKEN", default=None)
        if not token or token == "YOUR_TOKEN_HERE":
            self.stdout.write(self.style.ERROR("TELEGRAM_TOKEN is not set in .env"))
            return

        application = ApplicationBuilder().token(token).build()

        start_handler = CommandHandler("start", self.start)
        resumo_handler = CommandHandler("resumo", self.resumo)
        categoria_handler = CommandHandler("gastos_categoria", self.gastos_categoria)
        detalhe_handler = CommandHandler("detalhe", self.detalhe)

        application.add_handler(start_handler)
        application.add_handler(resumo_handler)
        application.add_handler(categoria_handler)
        application.add_handler(detalhe_handler)

        self.stdout.write(self.style.SUCCESS("Starting bot..."))
        application.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Olá! Sou o OrçamentoBot.\n"
            "Comandos disponíveis:\n"
            "/resumo - Total do mês\n"
            "/gastos_categoria - Total por categoria\n"
            "/detalhe <categoria> - Detalhes"
        )

    async def resumo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        now = timezone.now()
        # Async DB call
        total = await self.get_monthly_total(now.year, now.month)
        await update.message.reply_text(f"Total de gastos em {now.strftime('%B/%Y')}: R$ {total:.2f}")

    async def gastos_categoria(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        now = timezone.now()
        report = await self.get_category_report(now.year, now.month)
        if not report:
            await update.message.reply_text("Nenhum gasto encontrado neste mês.")
            return

        msg = f"Gastos por Categoria ({now.strftime('%B/%Y')}):\n"
        for item in report:
            msg += f"{item['category']}: R$ {item['total']:.2f}\n"
        await update.message.reply_text(msg)

    async def detalhe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Por favor, especifique a categoria. Ex: /detalhe Alimentação")
            return

        cat_name = " ".join(context.args)
        now = timezone.now()

        expenses = await self.get_category_details(cat_name, now.year, now.month)

        if not expenses:
            await update.message.reply_text(f"Nenhum gasto encontrado para '{cat_name}'.")
            return

        msg = f"Detalhes de '{cat_name}':\n"
        for desc, val in expenses:
            msg += f"- {desc}: R$ {val:.2f}\n"
        await update.message.reply_text(msg)

    @sync_to_async
    def get_monthly_total(self, year, month):
        result = Expense.objects.filter(transaction__date__year=year, transaction__date__month=month, is_ignored=False).aggregate(
            Sum("transaction__amount")
        )
        return result["transaction__amount__sum"] or 0

    @sync_to_async
    def get_category_report(self, year, month):
        expenses = Expense.objects.filter(transaction__date__year=year, transaction__date__month=month, is_ignored=False)
        report = []
        categories = Category.objects.all()
        for cat in categories:
            total = expenses.filter(category=cat).aggregate(Sum("transaction__amount"))["transaction__amount__sum"] or 0
            if total != 0:
                report.append({"category": cat.name, "total": total})
        return report

    @sync_to_async
    def get_category_details(self, category_name, year, month):
        # Case insensitive search for category?
        try:
            category = Category.objects.get(name__iexact=category_name)
        except Category.DoesNotExist:
            return []

        expenses = Expense.objects.filter(category=category, transaction__date__year=year, transaction__date__month=month, is_ignored=False)

        return [(e.description, e.transaction.amount) for e in expenses]
