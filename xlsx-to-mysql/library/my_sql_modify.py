from sqlalchemy import create_engine
from library import db_config as cf

def create_schema_if_not_exists():
    # MySQL 연결 엔진 생성
    engine = create_engine(f"mysql+mysqlconnector://{cf.db_id}:{cf.db_passwd}@{cf.db_ip}:{cf.db_port}")

    schema_name = cf.db_name

    # 스키마가 존재하는지 확인합니다.
    result = engine.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{schema_name}'")
    if not result.fetchone():
        # 스키마가 존재하지 않는 경우 생성합니다.
        engine.execute(f"CREATE DATABASE {schema_name}")
        print(f"'{schema_name}' 스키마가 존재하지 않아서 생성되었습니다.")

    # 연결을 닫습니다.
    engine.dispose()
