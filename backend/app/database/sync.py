import logging
from app.database.base import Base
import app.models  # noqa: F401

logger = logging.getLogger("blood_connect.db_sync")


def sync_sqlite_schema_sync(connection) -> None:
    """Inspect existing tables in SQLite and dynamically add any new columns declared on SQLAlchemy models."""
    try:
        raw_conn = connection.connection
        cursor = raw_conn.cursor()
        for table_name, table in Base.metadata.tables.items():
            cursor.execute(f"PRAGMA table_info({table_name})")
            rows = cursor.fetchall()
            if not rows:
                continue
            existing_cols = {row[1] for row in rows}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(connection.dialect)
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"
                    logger.info(f"Migrating SQLite table '{table_name}': adding column '{col.name}' ({col_type})")
                    cursor.execute(sql)
    except Exception as e:
        logger.warning(f"Error during SQLite schema sync: {e}")
