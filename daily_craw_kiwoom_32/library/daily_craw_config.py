import math
import pymysql
import datetime
from sqlalchemy import create_engine
import pandas as pd
from library import cf
from PyQt5.QtCore import *

pymysql.install_as_MySQLdb()

class daily_craw_config():
    def __init__(self, db_name, daily_craw_db_name, daily_buy_list_db_name):
        # db_name 0 인 경우는 simul 일때! 종목 데이터 가져오는 함수만 사용하기위해서
        if db_name != 0:
            self.db_name = db_name
            self.daily_craw_db_name = daily_craw_db_name

            self.daily_buy_list_db_name = daily_buy_list_db_name

            self.engine = create_engine(
                "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_craw",
                encoding='utf-8')
            self.daily_craw_db_con = self.engine.connect()

            self.get_item()
        else:
            pass

    # 불성실공시법인 가져오는 함수
    def get_item_insincerity(self):
        print("불성실 공시법인 리스트 Collect")

        self.code_df_insincerity = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=05', header=0)[0]
        # print(self.code_df_insincerity)

        # 6자리 만들고 앞에 0을 붙인다.
        self.code_df_insincerity.종목코드 = self.code_df_insincerity.종목코드.map('{:06d}'.format)

        # 우리가 필요한 것은 회사명과 종목코드이기 때문에 필요없는 column들은 제외해준다.
        self.code_df_insincerity = self.code_df_insincerity[['회사명', '종목코드']]

        # 한글로된 컬럼명을 영어로 바꿔준다.
        self.code_df_insincerity = self.code_df_insincerity.rename(columns={'회사명': 'code_name', '종목코드': 'code'})

    # 관리 종목을 가져오는 함수
    def get_item_managing(self):
        print("법정관리법인 리스트 Collect")
        self.code_df_managing = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=01', header=0)[0]  # 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌

        # 6자리 만들고 앞에 0을 붙인다.strPath --> str(unicode(strPath))
        self.code_df_managing.종목코드 = self.code_df_managing.종목코드.map('{:06d}'.format)

        # 우리가 필요한 것은 회사명과 종목코드이기 때문에 필요없는 column들은 제외해준다.
        self.code_df_managing = self.code_df_managing[['회사명', '종목코드']]

        # 한글로된 컬럼명을 영어로 바꿔준다.
        self.code_df_managing = self.code_df_managing.rename(columns={'회사명': 'code_name', '종목코드': 'code'})

    # KOSPI200 종목을 가져오는 함수
    def get_item_kospi(self):
        print("KOSPI200 지수 해당종목 Collect")
        self.code_df_kospi = \
        pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=06&marketType=stockMkt',header=0)[0]  # 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌

        # 6자리 만들고 앞에 0을 붙인다.
        self.code_df_kospi.종목코드 = self.code_df_kospi.종목코드.map('{:06d}'.format)

        # 우리가 필요한 것은 회사명과 종목코드이기 때문에 필요없는 column들은 제외해준다.
        self.code_df_kospi = self.code_df_kospi[['회사명', '종목코드']]

        # 한글로된 컬럼명을 영어로 바꿔준다.
        self.code_df_kospi = self.code_df_kospi.rename(columns={'회사명': 'code_name', '종목코드': 'code'})

    # KOSDAQ150 종목을 가져오는 함수
    def get_item_kosdaq(self):
        print("KOSDAQ150 지수 해당종목 Collect")
        self.code_df_kosdaq = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=16&marketType=kosdaqMkt',header=0)[0]  # 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌

        # 6자리 만들고 앞에 0을 붙인다.
        self.code_df_kosdaq.종목코드 = self.code_df_kosdaq.종목코드.map('{:06d}'.format)

        # 우리가 필요한 것은 회사명과 종목코드이기 때문에 필요없는 column들은 제외해준다.
        self.code_df_kosdaq = self.code_df_kosdaq[['회사명', '종목코드']]

        # 한글로된 컬럼명을 영어로 바꿔준다.
        self.code_df_kosdaq = self.code_df_kosdaq.rename(columns={'회사명': 'code_name', '종목코드': 'code'})

    # KRX300를 종목을 가져오는 함수
    def get_item(self):
        # print("KRX300 지수 해당종목 Collect")
        self.code_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=17', header=0)[0]  # 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌

        # 6자리 만들고 앞에 0을 붙인다.
        self.code_df.종목코드 = self.code_df.종목코드.map('{:06d}'.format)

        # 우리가 필요한 것은 회사명과 종목코드이기 때문에 필요없는 column들은 제외해준다.
        self.code_df = self.code_df[['회사명', '종목코드']]

        # 한글로된 컬럼명을 영어로 바꿔준다.
        self.code_df = self.code_df.rename(columns={'회사명': 'code_name', '종목코드': 'code'})

if __name__ == "__main__":
    daily_craw_config = daily_craw_config()

