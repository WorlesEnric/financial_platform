"""Alembic migrations subpackage.

The original stub re-exported from ``finance_platform.migrations.manager``
(MigrationManager, get_migration_manager, run_migrations, etc.), but
no ``manager.py`` was ever shipped under this subpackage. Nothing in
the rest of the build imports from ``finance_platform.migrations``,
so the re-export is removed and this file is left as a minimal
namespace marker. Alembic's own ``env.py`` and ``versions/`` layout
is unaffected. See ../../../problem.md.
"""
