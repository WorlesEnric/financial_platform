import asyncio
import click
from sqlmodel import select

from finance_platform.cli.main import cli
from finance_platform.config import get_settings
from finance_platform.db.session import get_async_engine, create_session_factory
from finance_platform.identity.models import Company


@cli.group()
def company():
    """Manage companies."""


@company.command()
@click.argument("name")
@click.argument("currency_code")
def create(name: str, currency_code: str) -> None:
    """Create a new company."""
    import uuid

    async def _run():
        engine = get_async_engine()
        factory = create_session_factory(engine)
        async with factory() as session:
            c = Company(id=uuid.uuid4(), name=name, currency_code=currency_code.upper())
            session.add(c)
            await session.commit()
            click.echo(f"Created company {c.id} — {c.name} ({c.currency_code})")

    asyncio.run(_run())


@company.command()
@click.argument("company_id")
def show(company_id: str) -> None:
    """Show company details."""
    from uuid import UUID

    async def _run():
        engine = get_async_engine()
        factory = create_session_factory(engine)
        async with factory() as session:
            stmt = select(Company).where(Company.id == UUID(company_id))
            result = await session.execute(stmt)
            c = result.scalar_one_or_none()
            if not c:
                click.echo(f"Company {company_id} not found.")
                return
            click.echo(f"ID:            {c.id}")
            click.echo(f"Name:          {c.name}")
            click.echo(f"Currency:      {c.currency_code}")
            click.echo(f"Active:        {c.is_active}")
            click.echo(f"Created:       {c.created_at}")
            click.echo(f"Updated:       {c.updated_at}")

    asyncio.run(_run())
