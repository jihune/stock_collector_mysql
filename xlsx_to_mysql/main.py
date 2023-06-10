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
        exit(1)

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

        # 0번째 열인 Index로 되어있는 열을 삭제합니다.
        sheet_data = sheet_data.iloc[:, 1:]

        # 중복된 행을 제거합니다.
        sheet_data = sheet_data.loc[:, ~sheet_data.columns.duplicated(keep='first')]

        # NaN, inf 값을 0으로 대체합니다.
        sheet_data = sheet_data.fillna(0)
        sheet_data = sheet_data.replace([np.inf, -np.inf], 0)

        # 종목코드 앞에 005930 일때 00이 날아가는 문제를 해결합니다.
        sheet_data['종목코드'] = sheet_data.종목코드.map('{:06d}'.format)

        # ROE가 반대로 하락하는 기업이라면 어떡할까요? 일단 S-RIM 공식을 사용하는 기업은 ROE가 지속적으로 하락하는 기업을 제외합니다.
        # 'average_roe' 열이 음수인 경우 'S_RIM', 'S_RIM_10', 'S_RIM_20' 열의 값을 모두 0으로 변경합니다.
        if 'average_roe' in sheet_data.columns:
            sheet_data.loc[sheet_data['average_roe'] < 0, ['S_RIM', 'S_RIM_10', 'S_RIM_20']] = 0

        # Rename columns if they exist
        # Convert columns to integer type
        if 'S-RIM 적정주가' in sheet_data.columns:
            sheet_data.rename(columns={'S-RIM 적정주가': 'S_RIM'}, inplace=True)
            sheet_data.rename(columns={'S-RIM -10%': 'S_RIM_10'}, inplace=True)
            sheet_data.rename(columns={'S-RIM -20%': 'S_RIM_20'}, inplace=True)

            # ROE 값이 BBB- 회사채 수익률(할인율)보다 작다면, 굳이 투자할 이유가 없다고 언급합니다.
            # 이 때는 경우에 따라 초과이익 지속 시에 해당하는 적정주가만 참조합니다.
            sheet_data.loc[sheet_data['S_RIM'] < sheet_data['S_RIM_10'], 'S_RIM_10'] = sheet_data['S_RIM']
            sheet_data.loc[sheet_data['S_RIM'] < sheet_data['S_RIM_20'], 'S_RIM_20'] = sheet_data['S_RIM']

            sheet_data['S_RIM'] = sheet_data['S_RIM'].astype(int)
            sheet_data['S_RIM_10'] = sheet_data['S_RIM_10'].astype(int)
            sheet_data['S_RIM_20'] = sheet_data['S_RIM_20'].astype(int)

        if 'S-RIM 괴리율' in sheet_data.columns:
            sheet_data.rename(columns={'S-RIM 괴리율': 'S_RIM_20_difr'}, inplace=True)
            sheet_data.loc[sheet_data['average_roe'] < 0, ['S_RIM_20_difr']] = 0

        # 데이터를 MySQL 테이블로 삽입합니다.
        sheet_data.to_sql(table_name, con=engine, if_exists='replace', index=False)

    print(f"xlsx의 Sheet들을 MySQl DB에 각 Table로 저장 성공")

    # 변경 사항을 커밋하고 engine 종료.
    engine.dispose()
