import pandas as pd
from sqlalchemy import create_engine
from library import db_config as cf
from library import my_sql_modify
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
import numpy as np

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    file_paths = askopenfilenames(title="Select Excel Files", filetypes=[("Excel Files", "*.xlsx")])
    file_paths = root.tk.splitlist(file_paths)
    print(f"선택된 파일 경로들: {file_paths}")

    if not file_paths:
        print("파일 선택이 취소되었습니다.")
        exit()

    # pandas를 사용하여 XLSX 파일에서 데이터를 읽습니다.
    xlsx_data = {}

    for file_path in file_paths:
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            if sheet_name in xlsx_data:
                xlsx_data[sheet_name] = pd.concat([xlsx_data[sheet_name], xls.parse(sheet_name)], ignore_index=True)
            else:
                xlsx_data[sheet_name] = xls.parse(sheet_name)

    print("파일 병합 완료")

    # 필요한 경우 스키마를 생성하기 위해 함수를 호출합니다.
    my_sql_modify.create_schema_if_not_exists()

    # MySQL 연결 엔진 생성
    engine = create_engine(f"mysql+mysqlconnector://{cf.db_id}:{cf.db_passwd}@{cf.db_ip}:{cf.db_port}/{cf.db_name}")
    print(f"DB 연결 성공")

    # 데이터를 MySQL 테이블에 삽입합니다.
    for sheet_name, sheet_data in xlsx_data.items():
        # 테이블 이름을 유효한 형식으로 변환합니다.
        table_name = sheet_name.replace(" ", "_")

        # 0번째 열을 삭제합니다.
        sheet_data = sheet_data.iloc[:, 1:]

        # 중복된 열을 제거합니다.
        sheet_data = sheet_data.loc[:, ~sheet_data.columns.duplicated()]

        # NaN 값을 0으로 대체합니다.
        sheet_data = sheet_data.fillna(0)

        # Replace 'inf' values with 0
        sheet_data = sheet_data.replace([np.inf, -np.inf], 0)

        # '종목번호' 열을 문자열로 변환합니다.
        if '종목번호' in sheet_data.columns:
            sheet_data['종목번호'] = sheet_data['종목번호'].astype(str)

        # 데이터를 MySQL 테이블로 삽입합니다.
        sheet_data.to_sql(table_name, con=engine, if_exists='replace', index=False)

    print(f"DB에 Table 저장 성공")

    # 변경 사항을 커밋하고 engine 종료.
    engine.dispose()
