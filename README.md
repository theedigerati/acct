## Acct

Manage invoices, bills, expenses, payments, acccounting books & more.

- 🧾 **Invoices & Clients** - Generate detailed invoices for clients.
- 🔖 **Bills & Vendors** - Record bills received from vendors.
- 🛍 **Expenses** - Record all expenditures.
- 💸 **Payments** - Manage payments received on invoices & payments made on bills.
- 📦 **Inventory** - Simple stock tracking for items.
- 📖 **Double-Entry Accounting** - Automatic debit & credit entries for every transaction.
- 📊 **Journals & Reports** - Manage accounting books, record manual journals & generate accounting reports.
- 🏭 **Multiple Organsations** - Multi-tenancy architecture with semi-isolated approach using [PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)

## Getting Started

This project uses Docker to simplify setup and development. To begin, ensure you have [Docker installed](https://docs.docker.com/get-started/get-docker/) on your machine.

1. **Clone the Repository**

```sh
git clone https://github.com/theedigerati/acct.git && cd acct
```

2. **Apply Django migrations**

Run database migrations to set up the initial schema:

```sh
docker compose run --rm python manage.py migrate
```

3. **Set Up Tenancy Data**

This will initialize a default tenant, create a basic chart of accounts, and provision the system owner.

```sh
docker compose run --rm python manage.py setup_tenancy
```
> ✅ A superuser account is created automatically with:
> **Email:** `owner@acct`
> **Password:** `owner`

4. **Start the Application**

```sh
docker compose up
```


## Access the application

To support multi-tenancy, each tenant is available via a custom subdomain, for example: `tenant1.example.com`.

### Local Development Setup

On a typical local machine, accessing subdomains would require manually adding entries to `/etc/hosts`. To streamline this, we use:
- [dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html) as a DNS resolver for a custom local domain with wildcard subdomain support.
- [nginx](https://nginx.org/) as a reverse proxy to serve the application on port `80`.

This setup allows seamless routing to tenant-specific domains without additional system configuration.

### Accessing URLs

- Public API - http://acct
- Default Tenant API - http://default.acct
- OpenAPI Docs - http://default.acct/docs
