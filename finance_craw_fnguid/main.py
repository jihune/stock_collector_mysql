from library import fnguide_collector

if __name__ == "__main__":
    # 오류 발생 시 README.txt 참조
    user_chice = input("특정 종목의 재무제표 수집 : 1 / 모든 종목의 재무제표 수집 : 2 => ")

    if user_chice == '1':
        fnguide_collector.get_stock_finance_table()

    elif user_chice == '2':
        fnguide_collector.get_many_stock_finance_table()

    else:
        print("1 또는 2 값만 입력하세요.")
        exit()

    print("\n재무제표 정보를 성공적으로 DB에 저장했습니다.")