from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, event

from app.config import db_path

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy 모델이 없어서 --autogenerate는 쓰지 않는다. 절차는 직접 쓴다.
target_metadata = None


def _url() -> str:
    # DB 위치는 app.config.db_path()가 정한다. 테스트용 DB는 TASKFLOW_DB로 지정한다.
    return f"sqlite:///{db_path().as_posix()}"


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url())

    # SQLite는 DDL도 트랜잭션에 넣으려면 직접 BEGIN을 해야 한다.
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, _record):
        dbapi_connection.isolation_level = None
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    @event.listens_for(engine, "begin")
    def _on_begin(conn):
        conn.exec_driver_sql("BEGIN")

    with engine.connect() as connection:
        # 리비전마다 한 트랜잭션이다. 확인이 맞지 않아 예외가 나면 그 리비전의 변경은 모두 취소된다.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
