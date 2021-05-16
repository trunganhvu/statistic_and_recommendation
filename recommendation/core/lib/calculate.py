# %%
import numpy as np
from scipy.spatial.distance import cosine as cosine_distance
import pandas as pd

# %%
def cosine_similarity(X: pd.DataFrame, y: pd.DataFrame=None):
    """ Độ đo cosin giữa các hàng của mt1 với các hàng của mt2
    """
    if y is None:
        y = np.array(X)
    sim_matrix = pd.DataFrame(
        np.array([[1 - cosine_distance(X.iloc[i], y.iloc[j]) for j in range(len(y))] for i in range(len(X))]))

    if hasattr(X, 'index'):
        sim_matrix.index = X.index
    if hasattr(y, 'index'):
        sim_matrix.columns = y.index

    return sim_matrix

def pearson_similarity(X, y):
    """ Độ đo pearson thể hiện sự động biến hoặc nghịch biến của 2 biến
    với dữ liệu đã chuẩn hóa về trung bình độ đo pearson và cosine sẽ cho cùng kết quả
    """
    sim_matrix = pd.DataFrame(np.corrcoef(X, y)).iloc[:len(X), -len(y):]

    if hasattr(X, 'index'):
        sim_matrix.index = X.index
    if hasattr(y, 'index'):
        sim_matrix.columns = y.index

    return sim_matrix


# if __name__ == '__main__':
#     mt1 = pd.DataFrame([[8,9,7,8,9,7],[6,5,3,8,9,7],[8,9,5,6,5,5]])
#     mt2 = pd.DataFrame([[6,7,4,5,4,2]])
#
#     print(pearson_similarity(mt1, mt2))