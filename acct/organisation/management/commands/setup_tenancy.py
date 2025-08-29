from django.conf import settings
from django.db import transaction
from django.core.management.base import BaseCommand
from apps.organisation.models import OrgAddress, Organisation, Tenant
from apps.user.models import User
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.tasks import provision_tenant
from apps.accounting.factory import AccountingFactory


class Command(BaseCommand):
    help = "Create public tenant and default Organisation."

    def handle(self, *args, **options):
        domain = settings.TENANT_USERS_DOMAIN
        public_owner = settings.BASE_TENANT_OWNER_EMAIL

        self.create_public_tenant(domain, public_owner)
        self.setup_default_organisation(public_owner)
        self.setup_default_resources()
        self.stdout.write("Tenancy setup done!")

    @transaction.atomic
    def create_public_tenant(self, domain, public_owner):
        if not Tenant.objects.filter(schema_name="public").exists():
            self.stdout.write("creating public tenant...")
            create_public_tenant(
                domain,
                public_owner,
                is_staff=True,
                is_superuser=True,
                first_name="John",
                last_name="Smith",
                role=User.OWNER,
                password="owner",
            )
            self.stdout.write(
                f"Public tenant created with {domain} as domain and {public_owner} as owner"
            )
        else:
            self.stdout.write("Public tenant already exists!")

    @transaction.atomic
    def setup_default_organisation(self, public_owner):
        if Organisation.objects.first() is None:
            self.stdout.write("creating default organisation...")
            org_slug = "acme"
            provision_tenant(
                tenant_name=org_slug,
                tenant_slug=org_slug,
                user_email=public_owner,
                is_staff=True,
            )
            tenant = Tenant.objects.get(slug=org_slug)
            address = OrgAddress.objects.create(
                line1="25 Rahman Str.",
                line2="Off B Road",
                city="Lekki",
                state="Lagos",
                postcode="100213",
                country="Nigeria",
            )
            org = Organisation.objects.create(
                name="Acme Inc.",
                address=address,
                tenant=tenant,
            )
            self.stdout.write(f"{org.name} has been created successfully")

            self.stdout.write("Creating default Financial Accounts...")
            accounting_factory = AccountingFactory(tenant.schema_name)
            accounting_factory.generate_default_accounts()
            self.stdout.write("Default accounts created successfully")

        else:
            self.stdout.write("Default organisation already exists!")

    @transaction.atomic()
    def setup_default_resources(self):
        self.stdout.write("Setting up  default resources...")
        for org in Organisation.objects.all():
            self.stdout.write(f"Creating default Financial Accounts for {org.name}...")
            accounting_factory = AccountingFactory(org.tenant.schema_name)
            accounting_factory.generate_default_accounts()
