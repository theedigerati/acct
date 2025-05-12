<div align="center">
  <h1>acct</h1>
</div>

[![Project Status: WIP](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

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

**1. Clone the Repository**

```sh
git clone https://github.com/theedigerati/acct.git && cd acct
```

**2. Apply Django Migrations**

Run database migrations to set up the initial schema:

```sh
docker compose run --rm api python manage.py migrate
```

**3. Set Up Tenancy Data**

This will initialize a default tenant, create a basic chart of accounts, and provision the system owner.

```sh
docker compose run --rm api python manage.py setup_tenancy
```
> ✅ A superuser account is created automatically with:  
> **Email:** `owner@acct`  
> **Password:** `owner`  

**4. Start the Application**

```sh
docker compose up
```


## Accessing the Application

To support multi-tenancy, each organisation(tenant) is available via a custom subdomain, for example: `tenant1.example.com`.

### Local Development Setup

To avoid manually adding each subdomain to `/etc/hosts`, this project uses:
- [dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html) as a DNS resolver for custom local domain with wildcard subdomain (i.e. `*.acct`).
- [Nginx](https://nginx.org/) as a reverse proxy to serve the application on port `80`.

These tools have been configured as docker services and should already be running after installation step 4. The only thing left to do, is to add the `resolver` configuration for our custom domain in `/etc/resolver/` (for linux/mac).

```sh
sudo mkdir /etc/resolver
sudo sh -c 'echo "nameserver 127.0.0.1" >> /etc/resolver/acct'
```

Basically, we're telling our host machine to search the nameserver on our localhost on port `53`, where our dnsmasq container is running.

This setup enables seamless access to subdomain-based tenants during local development.

### Accessing URLs

- Public API - http://acct
- Tenant API - http://acme.acct
- OpenAPI Docs - http://acme.acct/docs

Sub-domain slug can be customised for any organisation(tenant).
