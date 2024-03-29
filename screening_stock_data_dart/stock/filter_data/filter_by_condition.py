from array import array
import pandas as pd
import numpy as np

def filtering_data_that_specific_data(code_list: array, data: pd.DataFrame):
    """
    특정 기업만을 추출함.
    :param code_list:
    :param data:
    :return:
    """

    return data[data['종목코드'].isin(code_list)]


def filtering_data_that_market_cap_under(percent: float, data: pd.DataFrame):
    """
    코스피, 코스닥의 종목에서 시가총액 30%이하의 종목으로 필터함.
    이 때, 기업소재지가 외국, 스팩주, 우선주, 최신거래일에 거래량이 0인 종목은 제거함.
    :param data:
    :return: DataFrame
    """

    data = drop_volume(data)
    return data[data["시가총액"] <= data["시가총액"].quantile(q=percent)].sort_values(by=["시가총액"], ascending=True)


def filtering_data_that_market_cap_greater_than(percent: float, data: pd.DataFrame):
    """
    코스피, 코스닥의 종목에서 시가총액 특정 퍼센테이지 이상의 종목으로 필터함.
    이 때, 기업소재지가 외국, 스팩주, 우선주, 최신거래일에 거래량이 0인 종목은 제거함.
    :param data:
    :return: DataFrame
    """

    data = drop_volume(data)
    return data[data["시가총액"] > data["시가총액"].quantile(q=percent)].sort_values(by=["시가총액"], ascending=True)

def filtering_data_that_market_index_kospi200(data: pd.DataFrame):
    kospi200_data = pd.read_html(
        'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=06', header=0)[0]

    kospi200_data['종목코드'] = kospi200_data.종목코드.map('{:06d}'.format)

    merged_data = data.merge(kospi200_data, left_on='종목코드', right_on='종목코드', how='inner')

    return merged_data

def filtering_data_that_market_index_kosdaq150(data: pd.DataFrame):
    kosdaq150_data = pd.read_html(
        'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=16', header=0)[0]

    kosdaq150_data['종목코드'] = kosdaq150_data.종목코드.map('{:06d}'.format)

    merged_data = data.merge(kosdaq150_data, left_on='종목코드', right_on='종목코드', how='inner')

    return merged_data

def filtering_data_that_market_index_krx300(data: pd.DataFrame):
    krx300_data = pd.read_html(
        'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=17', header=0)[0]

    krx300_data['종목코드'] = krx300_data.종목코드.map('{:06d}'.format)

    merged_data = data.merge(krx300_data, left_on='종목코드', right_on='종목코드', how='inner')

    return merged_data

def filtering_low_per(sheet_name, df_copied: pd.DataFrame, all_data=False):
    """
    전체 데이터중 조회시점을 기준으로 PER가 10 이하인 기업.
    :param data:
    :return:
    """

    df = drop_volume(df_copied)
    df = df[df["PER"] > 0]

    if all_data:
        return (sheet_name,
                df[df["PER"] <= 10.0].sort_values(by=["PER"], ascending=[True]))
    else:
        return (sheet_name,
                df[df["PER"] <= 10.0].sort_values(by=["연도", "PER"], ascending=[False, True]))


def filtering_low_pbr_and_per(sheet_name, pbr: float, per: float, df: pd.DataFrame, all_data=False):
    """
    0.2 <= PBR < pbr
    0 < PER <= per
    :param pbr:
    :param per:
    :param df:
    :param all_data:
    :return:
    """

    df1 = df[df['PBR'].between(0.2, pbr)].copy()
    df2 = df1[df1['PER'].between(0.5, per)].copy()

    if all_data:
        df2["PBR rank"] = df2["PBR"].rank(ascending=True)
        df2["PER rank"] = df2["PER"].rank(ascending=True)
    else:
        df2["PBR rank"] = df2.groupby("연도")["PBR"].rank(ascending=True)
        df2["PER rank"] = df2.groupby("연도")["PER"].rank(ascending=True)

    df2["Total_rank"] = df2["PBR rank"] + df2["PER rank"]

    return (sheet_name,
            df2.sort_values(by=['Total_rank', '종목코드'], ascending=[True, True]).reset_index(
                drop=True)
            )


def filtering_low_psr_and_per(sheet_name, per: float, df: pd.DataFrame):
    """
    저 PSR
    0 < PER <= per
    :param pbr:
    :param per:
    :param df:
    :return:
    """

    df2 = df[df['분기 PER'].between(0.5, per)].copy()

    df2["PSR rank"] = df2.groupby("연도")["PSR"].rank(ascending=True)
    df2["PER rank"] = df2.groupby("연도")["분기 PER"].rank(ascending=True)

    df2["Total_rank"] = df2["PSR rank"] + df2["PER rank"]

    return (sheet_name,
            df2.sort_values(by=['연도', 'Total_rank'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_high_div(sheet_name, df: pd.DataFrame):
    """
    전체 데이터중 조회 시점으로 배당률이 0제외한 기업들에서 내림차순으로 정렬한 데이터.
    :param df:
    :return:
    """

    df.drop(
        df[df["DIV"] <= 0].index,
        inplace=True
    )

    return (sheet_name,
            df.sort_values(by=["DIV"], ascending=False).reset_index(drop=True)
            )

def filtering_peg(sheet_name, df: pd.DataFrame):
    """
    PEG, PER/이익 성장률
    최근분기 데이터로 계산
    :param sheent_name:
    :param df:
    :return:
    """

    df.drop(
        df[df["부채비율"] >= 400.0].index,
        inplace=True
    )
    df.drop(
        df[df["분기 PEG"] <= 0].index,
        inplace=True
    )

    peg_condition = (df['분기 PEG'] < 1.2)

    df2 = df[peg_condition]

    return (sheet_name,
            df2.sort_values(by=['연도', '분기 PEG'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_high_ncav_cap_and_gpa(sheet_name, df: pd.DataFrame):
    """
    청산가치/시가총액이 높고 GPA수치가 높은 기업들
    :param df:
    :return:
    """

    df.drop(
        df[df["당기순이익"] <= 0].index,
        inplace=True
    )

    df.drop(
        df[df["부채비율"] >= 200.0].index,
        inplace=True
    )

    df.drop(
        df[df["NCAV/MC"] <= 0.0].index,
        inplace=True
    )

    df["NCAV/MC rank"] = df.groupby("연도")["NCAV/MC"].rank(ascending=False)
    df["GP/A rank"] = df.groupby("연도")["GP/A"].rank(ascending=False)

    df["Total score"] = df["NCAV/MC rank"] + df["GP/A rank"]

    return (sheet_name,
            df.sort_values(by=['연도', "Total score"], ascending=[False, True]).reset_index(
                drop=True)
            )

def filtering_value_factor(sheet_name, df: pd.DataFrame):
    """
    PBR, PER, PCR, PSR의 합게 점수값이 낮은 순.
    강환국 슈퍼 가치전략
    분기 PER값을 사용
    :param df:
    :return:
    """

    df.drop(
        df[df["분기 PER"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PSR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PCR"] <= 0].index,
        inplace=True
    )

    df["PBR rank"] = df.groupby("연도")["PBR"].rank(ascending=True)
    df["PER rank"] = df.groupby("연도")["분기 PER"].rank(ascending=True)
    df["PCR rank"] = df.groupby("연도")["PCR"].rank(ascending=True)
    df["PSR rank"] = df.groupby("연도")["PSR"].rank(ascending=True)

    df["4 Total Value score"] = df["PBR rank"] + df["PER rank"] + df["PCR rank"] + df["PSR rank"]

    return (sheet_name,
            df.sort_values(by=['연도', '4 Total Value score'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_value_factor2(sheet_name, df: pd.DataFrame):
    """
    아래의 높은순 랭크
    - ROE, 영업이익률, 순이익률
    아래 낮은 순 랭크
    - 분기 PER, PBR, PCR, PSR, POR, PFCR, PGPR

    분기 PER값을 사용
    :param df:
    :return:
    """

    df.drop(
        df[df["분기 PER"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PCR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PSR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["POR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PGPR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["YoY 매출액 증가율"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["YoY 영업이익 증가율"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["YoY 당기순이익 증가율"] <= 0].index,
        inplace=True
    )

    df["ROE rank"] = df.groupby("연도")["분기 ROE"].rank(ascending=False)
    df["영업이익률 rank"] = df.groupby("연도")["영업이익률"].rank(ascending=False)
    df["순이익률 rank"] = df.groupby("연도")["당기순이익률"].rank(ascending=False)
    df["YoY 영업이익 증가율 rank"] = df.groupby("연도")["YoY 영업이익 증가율"].rank(ascending=False)
    df["YoY 당기순이익 증가율 rank"] = df.groupby("연도")["YoY 당기순이익 증가율"].rank(ascending=False)

    df["PBR rank"] = df.groupby("연도")["PBR"].rank(ascending=True)  # 기업 가치
    df["PER rank"] = df.groupby("연도")["분기 PER"].rank(ascending=True)  # 순자산
    df["PCR rank"] = df.groupby("연도")["PCR"].rank(ascending=True)  # 영업활동 현금흐름
    df["PFCR rank"] = df.groupby("연도")["PFCR"].rank(ascending=True)  # 잉여 현금흐름
    df["PSR rank"] = df.groupby("연도")["PSR"].rank(ascending=True)  # 매출
    df["POR rank"] = df.groupby("연도")["POR"].rank(ascending=True)  # 영업이익
    df["PGPR rank"] = df.groupby("연도")["PGPR"].rank(ascending=True)  # 메츨총이익

    df["Total Value score"] = \
        df["ROE rank"] + \
        df["영업이익률 rank"] + \
        df["순이익률 rank"] + \
        df["PBR rank"] + \
        df["PER rank"] + \
        df["PCR rank"] + \
        df["PSR rank"] + \
        df["POR rank"] + \
        df["PFCR rank"] + \
        df["PGPR rank"] + \
        df["YoY 영업이익 증가율 rank"] + \
        df["YoY 당기순이익 증가율 rank"]

    return (sheet_name,
            df.sort_values(by=['연도', 'Total Value score'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_value_factor3(sheet_name, df: pd.DataFrame):
    """
    PBR, PER, PGPR, PSR, POR의 합게 점수값이 낮은 순.
    분기 PER값을 사용
    :param df:
    :return:
    """

    df.drop(
        df[df["분기 PER"] <= 0].index,
        inplace=True
    )

    df.drop(
        df[df["PCR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PSR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["POR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PGPR"] <= 0].index,
        inplace=True
    )

    df.drop(
        df[df["YoY 당기순이익 증가율"] <= 0].index,
        inplace=True
    )

    df["PBR rank"] = df.groupby("연도")["PBR"].rank(ascending=True)  # 기업 가치
    df["PSR rank"] = df.groupby("연도")["PSR"].rank(ascending=True)  # 매출
    df["PGPR rank"] = df.groupby("연도")["PGPR"].rank(ascending=True)  # 매출총이익
    df["POR rank"] = df.groupby("연도")["PGPR"].rank(ascending=True)  # 영업이익
    df["PER rank"] = df.groupby("연도")["분기 PER"].rank(ascending=True)  # 순자산
    df["PEG rank"] = df.groupby("연도")["분기 PEG"].rank(ascending=True)  # 순자산의 성장률

    df["Total Value score"] = df["PBR rank"] + df["PSR rank"] + df["PGPR rank"] + df["POR rank"] + df["PER rank"] + df[
        "PEG rank"]

    return (sheet_name,
            df.sort_values(by=['연도', 'Total Value score'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_value_factor_upgrade(sheet_name, df: pd.DataFrame):
    """
    강환국 소형주 오리지널 슈퍼 가치 전략 업그레이드버전
    - 분기 PER
    - PBR
    - 분기 PFCR
    - 분기 PSR을 계산
    :param df:
    :return:
    """

    df.drop(
        df[df["분기 PER"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PFCR"] <= 0].index,
        inplace=True
    )
    df.drop(
        df[df["PSR"] <= 0].index,
        inplace=True
    )

    df["PBR rank"] = df.groupby("연도")["PBR"].rank(ascending=True)
    df["PER rank"] = df.groupby("연도")["분기 PER"].rank(ascending=True)
    df["PFCR rank"] = df.groupby("연도")["PFCR"].rank(ascending=True)
    df["PSR rank"] = df.groupby("연도")["PSR"].rank(ascending=True)

    df["4 Total Value score"] = df["PBR rank"] + df["PER rank"] + df["PFCR rank"] + df["PSR rank"]

    return (sheet_name,
            df.sort_values(by=['연도', '4 Total Value score'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_new_F_score_and_low_pbr(sheet_name, df: pd.DataFrame):
    """
    PBR하위 25퍼센트 중
    최근 1년간 신규주식 발행을 안했으며 -> 네이버증권 등에서 확인해야함.
    최신분기 순이익이 0이상인 기업
    최신분기 영업활동현금흐름이 0 이상인 기업
    :param df:
    :return:
    """

    df.drop(
        df[df["PBR"] <= df["PBR"].quantile(q=0.25)].index,
        inplace=True
    )

    df["당기순이익 점수"] = 0
    df["영업활동현금흐름 점수"] = 0

    df.loc[df["당기순이익"] > 0, "당기순이익 점수"] = 1
    df.loc[df["영업활동현금흐름"] > 0, "영업활동현금흐름 점수"] = 1

    df["F Score"] = df["당기순이익 점수"] + df["영업활동현금흐름 점수"]

    return (sheet_name,
            df.sort_values(by=['연도', 'F Score', 'PBR'], ascending=[False, False, True]).reset_index(
                drop=True)
            )


# def filtering_value_and_quality(sheet_name, pbr, df: pd.DataFrame):
#     """
#     유진 파마 교수 최종병기전략. p.282
#     0.25 < PBR < pbr
#     0.0 < GPA
#     자산성장률
#
#     :return: pd
#     """
#     # pbr_condition_1 = (df['PBR'] >= 0.25)
#     # pbr_condition_2 = (df['PBR'] <= pbr)
#     # gpa_condition = (df['GP/A'] > 0)
#
#     df1 = df[df['PBR'].between(0.25, pbr)].copy()
#
#     df1.drop(
#         df1[df1["GP/A"] <= 0].index,
#         inplace=True
#     )
#
#     # df2 = df2[df2["PBR"] <= df2["PBR"].quantile(q=0.5)]
#     # df2 = df2[df2["GP/A"] >= df2["GP/A"].quantile(q=0.75)]
#
#     df1["PBR rank"] = df1["PBR"].rank(ascending=True)
#     df1["GP/A rank"] = df1["GP/A"].rank(ascending=False)
#
#     df1["PBR_GP/A Score"] = df1["PBR rank"] + df1["GP/A rank"]
#
#     return (sheet_name,
#             df1.sort_values(by=['PBR_GP/A Score'], ascending=True).reset_index(
#                 drop=True)
#             )


def filtering_low_pfcr(sheet_name, df: pd.DataFrame):
    """
    PFCR. 시가총액 / 잉여현금흐름.
    작으면 주식이 저평가 되었다고 말할 수 있음.
    :param df:
    :return:
    """
    # df.drop(
    #     df[df["연도"] != latest_quarter].index,
    #     inplace=True
    # )

    df = df[df["PFCR"] > 0]

    return (sheet_name,
            df.sort_values(by=['연도', 'PFCR'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_profit_momentum(sheet_name, df: pd.DataFrame):
    """
    전분기 대비 당기영업이익 성장률 랭크
    전분기 대비 당기순이익 성장률 랭크
    :param df:
    :return:
    """

    df["당기영업이익 성장률 순위"] = df.groupby("연도")["QoQ 영업이익 증가율"].rank(method='min', ascending=False)
    df["당기순이익 성장률 순위"] = df.groupby("연도")["QoQ 당기순이익 증가율"].rank(method='min', ascending=False)

    df["모멘텀 순위"] = df["당기영업이익 성장률 순위"] + df["당기순이익 성장률 순위"]

    return (sheet_name,
            df.sort_values(by=['연도', '모멘텀 순위'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_value_and_profit_momentum(sheet_name, df: pd.DataFrame):
    """
    전분기 대비 당기영업이익 성장률 랭크
    전분기 대비 당기순이익 성장률 랭크
    분기 PER,
    PBR,
    PFCR,
    PSR
    :param df:
    :return:
    """

    df.drop(
        df[df["PSR"] <= 0].index,
        inplace=True
    )

    df["전년도 동기 대비 매출액 성장률 순위"] = df.groupby("연도")["YoY 매출액 증가율"].rank(method='min', ascending=False)
    df["전년도 동기 대비 영업이익 성장률 순위"] = df.groupby("연도")["YoY 영업이익 증가율"].rank(method='min', ascending=False)
    df["전년도 동기 대비 당기순이익 성장률 순위"] = df.groupby("연도")["YoY 당기순이익 증가율"].rank(method='min', ascending=False)

    df["PSR rank"] = df.groupby("연도")["PSR"].rank(ascending=True)
    df["PGPR rank"] = df.groupby("연도")["PGPR"].rank(ascending=True)
    df["POR rank"] = df.groupby("연도")["POR"].rank(ascending=True)
    df["PEG rank"] = df.groupby("연도")["분기 PEG"].rank(ascending=True)

    df["모멘텀 순위"] = (df["전년도 동기 대비 매출액 성장률 순위"] + df["전년도 동기 대비 영업이익 성장률 순위"] + df["전년도 동기 대비 당기순이익 성장률 순위"]
                    + df["PSR rank"] + df["PGPR rank"] + df["POR rank"] + df["PEG rank"]) / 7

    return (sheet_name,
            df.sort_values(by=['연도', '모멘텀 순위'], ascending=[False, True]).reset_index(
                drop=True)
            )


def filtering_s_rim_disparity_all_data(sheet_name, df: pd.DataFrame):

    df.loc[:, "S-RIM 괴리율"] = (df["종가"] - df["S-RIM 적정주가"]) / df["S-RIM 적정주가"] * 100
    df = df.replace([np.inf, -np.inf], 0)

    return (sheet_name,
            df.sort_values(by=["S-RIM 괴리율"], ascending=False).reset_index(drop=True)
            )


def filtering_s_rim_disparity_and_high_nav(sheet_name, df: pd.DataFrame):
    df.drop(
        df[df["NCAV/MC"] <= 0.0].index,
        inplace=True
    )

    df["연도"] = pd.to_datetime(df["연도"])

    latest_date = df["연도"].max()

    df = df[df["연도"] == latest_date].copy()

    df.loc[:, "S-RIM 괴리율"] = (df["종가"] - df["S-RIM 적정주가"]) / df["S-RIM 적정주가"] * 100
    df = df.replace([np.inf, -np.inf], 0)

    df.loc[:, "NCAV/MC rank"] = df["NCAV/MC"].rank(ascending=False)
    df.loc[:, "S-RIM 괴리율 rank"] = df["S-RIM 괴리율"].rank(ascending=True)

    df.loc[:, "Total score"] = df["NCAV/MC rank"] + df["S-RIM 괴리율 rank"]

    return (sheet_name,
            df.sort_values(by=["Total score"], ascending=True).reset_index(drop=True)
            )


def drop_column(df: pd.DataFrame):

    # 데이터 수집시 Drop할 주식들

    # 스팩 주식 드랍
    df.drop(
        df[df["종목명"].str.contains("스팩")].index,
        inplace=True
    )

    # 우선주, 리츠 드랍
    df.drop(
        df[df["종목명"].str.endswith(("1우", "2우", "우B", "우C", "(전환)", "리츠"))].index,
        inplace=True
    )

    # 2차적으로 우선주 삭제
    if '업종' in df.columns:
        df = df.drop(df[df['업종'].isna()].index)

    return df


def drop_volume(df: pd.DataFrame):
    # 직전 거래일의 거래량이 0인 경우는 어떠한 이유에서 거래정지가 되어있을 확률이 높음
    df = df[df["거래량"] > 0]

    return df
