import numpy as np
import pandas as pd


def fillNan(matrix: pd.DataFrame, type: str = 'value', value: float = 0):
    """
    :param matrix:
    :param type: lựa chọn ['value', 'col_avg', 'row_avg']
    :param value: float
    :return:
    """
    filled_matrix = matrix.isna()
    result_matrix = matrix.copy()

    if type == 'value':
        result_matrix = matrix.fillna(value)
    elif type == 'col_avg':
        col_avg = matrix.mean(axis=0)
        result_matrix = matrix.fillna(col_avg)
    elif type == 'row_avg':
        row_avg = matrix.mean(axis=1)
        result_matrix = matrix.T.fillna(row_avg).T

    return result_matrix, filled_matrix


def normalize(matrix: pd.DataFrame, type: str = 'col_avg'):
    """
    :param matrix:
    :param type: lựa chọn ['col_avg', 'row_avg']
    :return: ma trận chuẩn hóa giá trị trung bình theo cột hoặc hàng
    """
    if type == 'row_avg':
        avg_list = np.nanmean(matrix, axis=1)
        avg_list = np.array([avg_list]).T
        result_matrix = matrix - avg_list
    else:
        avg_list = np.nanmean(matrix, axis=0)
        result_matrix = matrix - avg_list

    return result_matrix, avg_list


def unnormalize(matrix: pd.DataFrame, avg_list: pd.Series, type: str = 'col_avg'):
    """
    :param matrix:
    :avg_list:
    :param type: lựa chọn ['col_avg', 'row_avg']
    :return:
    """
    result_matrix = matrix + avg_list

    return result_matrix


def formal_score(scoreboard: pd.DataFrame):
    """
    fix all grade to range from 0 to 10
    :param scoreboard:
    :return:
    """
    for i, row in scoreboard.iterrows():
        for col in scoreboard.columns:
            if row.loc[col] < 0:
                row.loc[col] = 0
            elif row.loc[col] > 10:
                row.loc[col] = 10
    return scoreboard


