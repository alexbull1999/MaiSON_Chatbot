# Database Migrations

This directory contains database migrations managed by Alembic.

## Creating a New Migration

To create a new migration:

```bash
alembic revision --autogenerate -m "description of the changes"
```

## Running Migrations

To apply all pending migrations:

```bash
alembic upgrade head
```

To rollback the last migration:

```bash
alembic downgrade -1
```

## Migration History

To view migration history:

```bash
alembic history
``` 