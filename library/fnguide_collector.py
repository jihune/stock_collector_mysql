import requests as re
from bs4 import BeautifulSoup
from pandas import DataFrame
from sqlalchemy import create_engine
import time

# cf = DB 정보를 담은 mysql-config 파일
from . import db_config as cf
from . import kind_stock_list
from . import my_sql_modify

def get_stock_finance_table():
    # 사용자 입력 받기
    ticker = input("회사명 또는 종목코드를 입력하세요 => ")

    # 종목 리스트를 KIND 사이트에서 받아옴
    tickers = kind_stock_list.collect_stock_list()

    if ticker in tickers.keys() or ticker in tickers.values():

        # 내 DB서버에 db_name이 없을 경우 생성, 이미 있다면 건너뜀
        my_sql_modify.create_database()

        print("\nDB연결 시작")
        engine = create_engine(
            "mysql+pymysql://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port
            + "/" + cf.db_name, encoding='utf-8')
        print("DB연결 성공")

        # 입력받은게 종목번호가 아니라 종목이름일 경우
        if ticker in tickers.values():
            flipped_tickers = dict((value, key) for key, value in tickers.items())
            code = flipped_tickers[ticker]
        else:
            code = ticker

        print(f"\n현재 정보 수집중인 종목: {tickers[code]}")

        ''' 경로 탐색'''
        url = re.get('http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A%s' % (code))
        url = url.content

        html = BeautifulSoup(url, 'html.parser')
        body = html.find('body')

        try:
            fn_body = body.find('div', {'class': 'fng_body asp_body'})
            ur_table = fn_body.find('div', {'id': 'div15'})
            table = ur_table.find('div', {'id': 'highlight_D_Y'})

            tbody = table.find('tbody')

            tr = tbody.find_all('tr')

            finance_table = DataFrame()

        except:
            print('에러가 발생했습니다.')
            print('해당 자료를 건너뜁니다.')
            return

        for i in tr:

            ''' 자료 항목 가져오기'''
            category = i.find('span', {'class': 'txt_acd'})

            if category == None:
                category = i.find('th')

            category = category.text.strip()

            '''값 가져오기'''
            value_list = []

            j = i.find_all('td', {'class': 'r'})

            for value in j:
                temp = value.text.replace(',', '').strip()

                try:
                    temp = float(temp)
                    value_list.append(temp)
                except:
                    value_list.append(0)

            finance_table['%s' % (category)] = value_list

            ''' 기간 가져오기 '''

            thead = table.find('thead')
            tr_2 = thead.find('tr', {'class': 'td_gapcolor2'}).find_all('th')

            year_list = []

            for i in tr_2:
                try:
                    temp_year = i.find('span', {'class': 'txt_acd'}).text
                except:
                    temp_year = i.text

                year_list.append(temp_year)

            finance_table.index = year_list

        finance_table = finance_table.T
        finance_table.insert(0, 'IFRS', finance_table.index)

        try:
            ''' DB에 저장'''
            finance_table.to_sql(name=tickers[code], con=engine, if_exists='replace', index=False)
            print(f"{tickers[code]} 종목의 재무제표를 성공적으로 저장하였습니다.")
        except Exception as e:
            print(f"{tickers[code]} 재무제표 저장 중 에러 발생: {e}")

        engine.dispose()

    else:
        print("입력한 값이 현재 찾을 수 있는 종목 리스트에 없습니다.")
        exit()


def get_many_stock_finance_table():

    # 내 DB서버에 db_name이 없을 경우 생성, 이미 있다면 건너뜀
    my_sql_modify.create_database()

    print("\nDB연결 시작")

    engine = create_engine(
        "mysql+pymysql://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port
        + "/" + cf.db_name, encoding='utf-8')
    print("DB연결 성공")

    # 종목 리스트를 KIND 사이트에서 받아옴
    tickers = kind_stock_list.collect_many_stock_list()

    # DB 저장 에러 발생 수 카운트
    err_count = 0
    err_tickers = []

    # 현재 몇번째 종목인지 인덱스
    index_ = 0

    for code in tickers.keys():

        index_ += 1
        print(f"\n현재 정보 수집중인 {index_}번째 종목: {tickers[code]}")

        ''' 경로 탐색'''
        url = re.get('http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A%s' % (code))
        url = url.content

        html = BeautifulSoup(url, 'html.parser')
        body = html.find('body')

        try:
            fn_body = body.find('div', {'class': 'fng_body asp_body'})
            ur_table = fn_body.find('div', {'id': 'div15'})
            table = ur_table.find('div', {'id': 'highlight_D_Y'})

            tbody = table.find('tbody')

            tr = tbody.find_all('tr')

            finance_table = DataFrame()

        except:
            print('에러가 발생했습니다.')
            print('해당 자료를 건너뜁니다.')
            continue

        for i in tr:

            ''' 자료 항목 가져오기'''
            category = i.find('span', {'class': 'txt_acd'})

            if category == None:
                category = i.find('th')

            category = category.text.strip()

            '''값 가져오기'''
            value_list = []

            j = i.find_all('td', {'class': 'r'})

            for value in j:
                temp = value.text.replace(',', '').strip()

                try:
                    temp = float(temp)
                    value_list.append(temp)
                except:
                    value_list.append(0)

            finance_table['%s' % (category)] = value_list

            ''' 기간 가져오기 '''

            thead = table.find('thead')
            tr_2 = thead.find('tr', {'class': 'td_gapcolor2'}).find_all('th')

            year_list = []

            for i in tr_2:
                try:
                    temp_year = i.find('span', {'class': 'txt_acd'}).text
                except:
                    temp_year = i.text

                year_list.append(temp_year)

            finance_table.index = year_list

        finance_table = finance_table.T
        finance_table.insert(0, 'IFRS', finance_table.index)

        try:
            ''' DB에 저장'''
            finance_table.to_sql(name=tickers[code], con=engine, if_exists='replace', index=False)
            print(f"{tickers[code]} 종목의 재무제표를 성공적으로 저장하였습니다.")
            time.sleep(0.3)
        except Exception as e:
            err_count += 1
            print(f"{tickers[code]} 재무제표 저장 중 에러 발생: {e}")
            print("10초간 크롤링 대기")
            err_tickers.append(tickers[code])
            time.sleep(10)

    engine.dispose()

    print('\nDB 저장 과정에서 오류가 %s번 발생하였습니다.' % (err_count))
    if err_tickers:
        print(f"저장 과정에서 오류가 발생한 종목: {err_tickers}")
