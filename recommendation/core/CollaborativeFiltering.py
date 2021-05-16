# coding=utf-8
import pandas as pd
from .lib import calculate, process


class CollaborativeFiltering_UB:
    param = {
        'knn': {
            'description': "K nearest neighbors",
            'type': 'int',
            'default': 10,
        },
        'nor': {
            'description': "normalize type",
            'type': 'str',
            'default': 'row_avg',
            'options': [
                'row_avg',
                'col_avg'
            ]
        },
        'sim': {
            'description': "type of similarity",
            'type': 'str',
            'default': 'cosine',
            'options': [
                'cosine',
                'pearson'
            ]
        }
    }

    def __init__(self, knn=10, nor: str = 'row_avg', sim='cosine'):  # Thiết đặt trọng số
        """
        :param nor:
        :param knn: K nearest neighbors
        :param sim: type of similarity 'cosine' or 'pearson'
        """
        self.data = None
        self.nor_type = nor
        if knn is not None and knn < 1:
            print("knn can't smaller than 1, auto set to 1")
            knn = 1
        self.k = knn
        if sim == "pearson":
            self.sim = calculate.pearson_similarity
        else:
            self.sim = calculate.cosine_similarity
        # print(sim)


    def fit(self, data):
        """import core data use to prediction"""
        # .dropna(axis=1,how='all')
        if type(data) == str:
            data = pd.read_csv(open(data, 'r', encoding='utf-8'))
        else:
            data = pd.DataFrame(data.copy())

        # required preprocess data to avoid error
        data = data.dropna(axis=1, thresh=10).dropna(axis=0, thresh=5)

        self.data = data

    def predict(self, user_score: pd.DataFrame, course_need_pre: list = None):
        #   clear user score
        if len(user_score) > 1:
            user_score = user_score[0:1]

        # clear input data
        user_score = user_score.dropna(axis=1)
        valid_course = list(set(user_score.columns) & set(self.data.columns))
        user_score = user_score[valid_course]
        del valid_course

        # course_need_pre == none -> all course
        if course_need_pre is None or len(course_need_pre) < 1:
            course_need_pre = set(self.data.columns)
        else:
            course_need_pre = [c for c in course_need_pre if c in self.data.columns]

        course_need_pre = list(set(course_need_pre) - set(user_score.columns))
        all_course = list(set(list(user_score.columns) + list(course_need_pre)))

        train_data = self.data.loc[:, all_course].dropna(axis=0, thresh=2)
        # end clear data

        # preprocessing: normalize and fill nan
        train_for_sim, filled_matrix = process.fillNan(train_data, type=self.nor_type)

        # Tính độ tương tự
        similarity_df = self.sim(train_for_sim.loc[:, user_score.columns], user_score)
        del train_for_sim

        # normalize
        train_nor, train_avg = process.normalize(train_data, 'row_avg')  # row_avg
        user_score_nor, user_avg = process.normalize(user_score, 'row_avg')

        # Dự đoán điểm, khởi tạo pre_score_nor
        pre_score_nor = pd.DataFrame(columns=course_need_pre, index=user_score.index)

        for col in course_need_pre:
            # lấy những điểm thật
            score_series = train_nor.loc[:, col].dropna()

            # lấy độ tương tự với những sinh viên có điểm trong score_series
            k_sim = similarity_df.loc[score_series.index, user_score.index[0]]

            if self.k is not None:
                k_sim = k_sim.nlargest(self.k)
                score_series = score_series.loc[k_sim.index.tolist()]

            # tính điểm dự đoán
            pre_score_nor.loc[user_score.index, col] = k_sim.mul(score_series).sum() / k_sim.sum()

        # unnormalize pre_score_nor
        pre_score = process.unnormalize(pre_score_nor, user_avg, 'row_avg')

        # Sửa lỗi điểm dự đoán
        return process.formal_score(pre_score)


class CollaborativeFiltering_IB:
    param = {
        'knn': {
            'description': "K nearest neighbors",
            'type': 'int',
            'default': 5,
        },
        'nor': {
            'description': "normalize type",
            'type': 'str',
            'default': 'col_avg',
            'options': [
                'col_avg',
                'row_avg'
            ]
        },
        'sim': {
            'description': "type of similarity",
            'type': 'str',
            'default': 'cosine',
            'options': [
                'cosine',
                'pearson'
            ]
        }
    }

    def __init__(self, knn=5, nor: str = 'col_avg', sim='cosine'):
        """ thiết đặt thông số cho mô hình
        @param knn: k nearest neighbor, k student have largest will be use to predict score
        @param nor: normalize type, use to normalize and fill na before calculate similarity
        @param sim: type of similarity 'cosine' or 'pearson'
        """
        self.data = None
        self.nor_type = nor
        if knn is not None and knn < 1:
            print("knn can't smaller than 1, auto set to 1")
            knn = 1
        self.k = knn
        self.similarity_df = None
        self.train_avg = None
        if sim == "pearson":
            self.sim = calculate.pearson_similarity
        else:
            self.sim = calculate.cosine_similarity
        self.attributes = ['nor_type', 'k']

    def fit(self, data):
        """import core data use to prediction"""
        if type(data) == str:
            data = pd.read_csv(open(data, 'r', encoding='utf-8'))
        else:
            data = pd.DataFrame(data.copy())

        # required preprocess data to avoid error
        data = data.dropna(axis=1, thresh=10).dropna(axis=0, thresh=5)
        # Mục tiêu là dữ liệu huấn luyện thì các hàng phải có nhiều hơn hoặc bằng 5 điểm của các môn khác nhau, còn các
        # cột phải có nhiều hơn hoặc bằng 10 điểm của các sinh viên khác nhau.

        self.data = data

        # preprocessing: normalize and fill nan
        train_for_sim, filled_matrix = process.fillNan(data, type=self.nor_type)
        # Tính độ tương tự
        self.similarity_df = self.sim(train_for_sim.T, train_for_sim.T)

        # normalize
        train_nor, train_avg = process.normalize(data, 'col_avg')  # row_avg
        self.train_avg = pd.DataFrame([train_avg], columns=data.columns)

    def predict(self, user_score: pd.DataFrame, course_need_pre: list = None):
        #   clear user score
        if len(user_score) > 1:
            user_score = user_score[0:1]

        # clear input data
        user_score = user_score.dropna(axis=1)
        valid_course = list(set(user_score.columns) & set(self.data.columns))
        user_score = user_score[valid_course]
        del valid_course

        # course_need_pre == none -> all course
        if course_need_pre is None or len(course_need_pre) < 1:
            course_need_pre = set(self.data.columns)
        else:
            course_need_pre = [c for c in course_need_pre if c in self.data.columns]

        # end clear data
        # Độ tương tự đã tính trong hàm fit()
        # lấy trung bình cột của train data để chuẩn hóa
        user_score_nor = user_score - self.train_avg.loc[[0], user_score.columns].values
        course_need_pre = list(set(course_need_pre) - set(user_score.columns))

        # Dự đoán điểm, khởi tạo pre_score_nor
        pre_score_nor = pd.DataFrame(columns=course_need_pre, index=user_score.index)
        # lấy những điểm thật
        score_series = user_score_nor.dropna(axis=1)

        for col in course_need_pre:

            # lấy độ tương tự với những sinh viên có điểm trong score_series
            k_sim = self.similarity_df.loc[[col], score_series.columns]

            if self.k is not None:
                k_sim = k_sim.nlargest(self.k)
                score_series = score_series.loc[:, k_sim.index.tolist()]

            # tính điểm dự đoán
            # print(k_sim, score_series.values)
            pre_score_nor.loc[user_score.index, col] = float(k_sim.mul(score_series.values).sum(axis=1) / k_sim.sum(axis=1))

        # unnormalize pre_score_nor
        pre_score = process.unnormalize(pre_score_nor, self.train_avg[course_need_pre].values, 'col_avg')

        # Sửa lỗi điểm dự đoán
        return process.formal_score(pre_score)

