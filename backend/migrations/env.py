from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.config import database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy 모델이 없어서 --autogenerate는 쓰지 않는다. 절차는 직접 쓴다.
target_metadata = None


def _url() -> str:
    # DB 주소는 app.config.database_url()이 정한다. (환경변수 DATABASE_URL)
    # SQLAlchemy가 psycopg(3) 드라이버를 쓰도록 주소 앞부분을 맞춘다.
    url = database_url()
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url())

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
