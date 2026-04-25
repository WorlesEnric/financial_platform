import asyncio
import click
from sqlmodel import select
from uuid import UUID

from finance_platform.cli.main import cli
from finance_platform.db.session import get_async_engine, create_session_factory
from finance_platform.models.approval import Approval
from finance_platform.models.expense import Expense


@cli.group()
def approval():
    """Manage approvals."""


@approval.command()
@click.argument("approval_id")
def show(approval_id: str) -> None:
    """Show approval details."""
    async def _run():
        engine = get_async_engine()
        factory = create_session_factory(engine)
        async with factory() as session:
            stmt = select(Approval, Expense).join(Expense, Approval.expense_id == Expense.id).where(Approval.id == UUID(approval_id))
            result = await session.execute(stmt)
            row = result.one_or_none()
            if not row:
                click.echo(f"Approval {approval_id} not found.")
                return
            a, e = row
            click.echo(f"ID:            {a.id}")
            click.echo(f"Expense:       {e.description} ({a.expense_id})")
            click.echo(f"Reviewer:      {a.reviewer_user_id}")
            click.echo(f"Status:        {a.status}")
            click.echo(f"Comment:       {a.comment or ''}")
            click.echo(f"Created:       {a.created_at}")
            click.echo(f"Updated:       {a.updated_at}")

    asyncio.run(_run())


@approval.command()
@click.option("--expense-id", required=True, help="Expense UUID")
@click.option("--reviewer-id", required=True, help="Reviewer user UUID")
@click.option("--status", default="PENDING", help="Approval status")
def create(expense_id: str, reviewer_id: str, status: str) -> None:
    """Create a new approval record."""
    import uuid

    async def _run():
        engine = get_async_engine()
        factory = create_session_factory(engine)
        async with factory() as session:
            a = Approval(
                id=uuid.uuid4(),
                expense_id=UUID(expense_id),
                reviewer_user_id=UUID(reviewer_id),
                status=status,
            )
            session.add(a)
            await session.commit()
            click.echo(f"Created approval {a.id} — status={a.status}")

    asyncio.run(_run())
