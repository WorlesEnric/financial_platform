import asyncio
import click
from sqlmodel import select
from uuid import UUID

from finance_platform.cli.main import cli
from finance_platform.db.session import get_async_engine, create_session_factory
from finance_platform.models.expense import Expense
from finance_platform.identity.models import Company


@cli.group()
def expense():
    """Manage expenses."""


@expense.command()
@click.argument("expense_id")
def show(expense_id: str) -> None:
    """Show expense details."""
    async def _run():
        engine = get_async_engine()
        factory = create_session_factory(engine)
        async with factory() as session:
            stmt = select(Expense, Company).join(Company, Expense.company_id == Company.id).where(Expense.id == UUID(expense_id))
            result = await session.execute(stmt)
            row = result.one_or_none()
            if not row:
                click.echo(f"Expense {expense_id} not found.")
                return
            e, c = row
            click.echo(f"ID:            {e.id}")
            click.echo(f"Company:       {c.name} ({c.id})")
            click.echo(f"Description:   {e.description}")
            click.echo(f"Amount Minor:  {e.amount_minor}")
            click.echo(f"Currency:      {e.currency_code}")
            click.echo(f"Status:        {e.status}")
            click.echo(f"Category:      {e.category}")
            click.echo(f"Submitted By:  {e.submitted_by_user_id}")
            click.echo(f"Created:       {e.created_at}")
            click.echo(f"Updated:       {e.updated_at}")

    asyncio.run(_run())


@expense.command()
@click.option("--company-id", required=True, help="Filter by company")
@click.option("--status", default=None, help="Filter by status")
@click.option("--limit", default=50, type=int, help="Max results")
def list(company_id: str, status: str | None, limit: int) -> None:
    """List expenses, optionally filtered."""
    async def _run():
        engine = get_async_engine()
        factory = create_session_factory(engine)
        async with factory() as session:
            stmt = select(Expense).where(Expense.company_id == UUID(company_id))
            if status:
                stmt = stmt.where(Expense.status == status)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            expenses = result.scalars().all()
            if not expenses:
                click.echo("No expenses found.")
                return
            click.echo(f"{'ID':<38} {'Amount Minor':<15} {'Status':<20} {'Category':<20}")
            click.echo("-" * 95)
            for e in expenses:
                click.echo(f"{str(e.id):<38} {e.amount_minor:<15} {e.status:<20} {e.category:<20}")

    asyncio.run(_run())
