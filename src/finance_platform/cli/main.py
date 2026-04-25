import sys
import uvicorn
import alembic.config
import alembic.command
import click
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from finance_platform.config import get_settings
from finance_platform.db.session import get_async_engine, create_session_factory
from finance_platform.identity.models import Company
from finance_platform.models.expense import Expense
from finance_platform.approvals.models import Approval


@click.group()
@click.version_option("0.1.0")
def cli():
    """finance-platform — Enterprise Financial Reimbursement + Amortization Platform."""


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind address")
@click.option("--port", default=8000, show_default=True, type=int, help="Port")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload")
def run_server(host: str, port: int, reload: bool) -> None:
    """Start the FastAPI development server."""
    from finance_platform import create_app
    app = create_app()
    click.echo(f"Starting server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)


@cli.command()
@click.argument("revision", default="head")
@click.option("--sql", is_flag=False, default=False, help="Only print SQL")
def migrate(revision: str, sql: bool) -> None:
    """Apply alembic database migrations up to REVISION (default: head)."""
    cfg = alembic.config.Config("alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    if sql:
        cfg.set_main_option("sqlalchemy.url", "sqlite://")
        alembic.command.upgrade(cfg, revision, sql=True)
    else:
        alembic.command.upgrade(cfg, revision)
    click.echo(f"Migrations applied up to {revision}")


@cli.command()
@click.option("--company-id", type=str, default=None, help="Run for a single company")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without persisting")
def month_end_close(company_id: str | None, dry_run: bool) -> None:
    """Run month-end-close: carry-forward, amortization tick, settlement sweep."""
    import asyncio
    from finance_platform.services import close_month

    async def _run():
        engine = get_async_engine()
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            result = await close_month(session, company_id=company_id, dry_run=dry_run)
            click.echo(f"Month-end close {'(dry-run) ' if dry_run else ''}completed:")
            for k, v in result.items():
                click.echo(f"  {k}: {v}")

    asyncio.run(_run())


@cli.command()
def seed_fixtures() -> None:
    """Seed the database with demo companies, users, and sample expenses."""
    import asyncio
    from finance_platform.db.session import get_async_engine, create_session_factory
    from finance_platform.services import seed_demo_data

    async def _run():
        engine = get_async_engine()
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            counts = await seed_demo_data(session)
            await session.commit()
            for k, v in counts.items():
                click.echo(f"  {k}: {v}")

    click.echo("Seeding demo data...")
    asyncio.run(_run())
    click.echo("Done.")


@cli.command()
def list_companies() -> None:
    """List all registered companies."""
    import asyncio

    async def _run():
        settings = get_settings()
        engine = get_async_engine()
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            stmt = select(Company)
            result = await session.execute(stmt)
            companies = result.scalars().all()
            if not companies:
                click.echo("No companies found.")
                return
            click.echo(f"{'ID':<38} {'Name':<30} {'Currency':<8}")
            click.echo("-" * 80)
            for c in companies:
                click.echo(f"{str(c.id):<38} {c.name:<30} {c.currency_code:<8}")

    asyncio.run(_run())


@cli.command()
def list_pending_approvals() -> None:
    """List all pending approvals across all companies."""
    import asyncio

    async def _run():
        engine = get_async_engine()
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            stmt = (
                select(Approval, Expense, Company)
                .join(Expense, Approval.expense_id == Expense.id)
                .join(Company, Expense.company_id == Company.id)
                .where(Approval.status == "PENDING")
                .limit(100)
            )
            result = await session.execute(stmt)
            rows = result.all()
            if not rows:
                click.echo("No pending approvals.")
                return
            click.echo(f"{'Approval ID':<38} {'Expense ID':<38} {'Company':<20} {'Amount Minor':<15} {'Status':<12}")
            click.echo("-" * 130)
            for approval, expense, company in rows:
                click.echo(
                    f"{str(approval.id):<38} {str(expense.id):<38} {company.name:<20} "
                    f"{expense.amount_minor:<15} {approval.status:<12}"
                )

    asyncio.run(_run())


def main() -> None:
    cli()
