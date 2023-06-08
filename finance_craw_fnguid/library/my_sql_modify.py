import pymysql
from . import db_config as cf

def create_database():
    # DB 연결 정보

    conn = pymysql.connect(
        host=cf.db_ip,
        user=cf.db_id,
        password=cf.db_passwd,
        port=int(cf.db_port)
    )

    try:
        with conn.cursor() as cursor:
            # 스키마 생성 쿼리
            create_schema_query = f"CREATE DATABASE IF NOT EXISTS {cf.db_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"

            # 스키마 생성 실행
            cursor.execute(create_schema_query)
    finally:
        conn.close()
