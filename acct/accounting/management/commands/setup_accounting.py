from django.core.management.base import BaseCommand
from apps.accounting.factory import AccountingFactory


class Command(BaseCommand):
    help = "Create the default accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "schema_name", help="The tenant schema to create accounts in."
        )

    def handle(self, *args, **options):
        schema_name = options["schema_name"]
        accounting_factory = AccountingFactory(schema_name)
        accounting_factory.generate_default_accounts()
