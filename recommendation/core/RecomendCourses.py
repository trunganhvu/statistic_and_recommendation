import pandas as pd
import json

from .lib import calculate, process
from .CollaborativeFiltering import CollaborativeFiltering_IB as CF_IB
from .CollaborativeFiltering import CollaborativeFiltering_UB as CF_UB
from .MatrixFactorization import MatrixFactorization as MF

SEMESTER_DICT = json.load(open("../data/input/semester_courses.json", 'r'))


def greatest_scoreCR(user_score, model, semester=None, k=5):
    course_need_pre = None
    if semester is not None:
        course_need_pre = SEMESTER_DICT[str(semester)]

    result = model.predict(user_score, course_need_pre).T
    result.columns = ["scores"]
    result['scores'] = result['scores'].astype('float')
    # print(result.nlargest(k, 'scores').round(2).T)
    return list(result.nlargest(k, 'scores').index)


def similar_neighborCR(user_score, data, model, semester=None, k=5, sim='cosine'):
    if sim == 'pearson':
        sim = calculate.pearson_similarity
    else:
        sim = calculate.cosine_similarity

    # make data have higher density
    data = data.dropna(axis=1, thresh=5).dropna(axis=0, thresh=5)
    data, filled_matrix = process.fillNan(data, type="row_avg")

    # leaned matrix of all student in data
    learned = filled_matrix.astype(int).replace(1, -1).replace(0, 1)

    #   clear user score
    if len(user_score) > 1:
        user_score = user_score[0:1]

    # clear input data
    user_score = model.predict(user_score)
    user_score = user_score.dropna(axis=1)
    user_score = user_score[list(set(user_score.columns) & set(data.columns))]

    # get unleaned course of user
    if semester is not None:
        course_list = [c for c in SEMESTER_DICT[str(semester)] if
                       (c in data.columns) and (c not in user_score.columns)]
    else:
        course_list = [c for c in data.columns if c not in user_score.columns]

    similarity_df = sim(data.loc[:, user_score.columns], user_score)

    result = (similarity_df.values * learned[course_list]).sum() / len(data)
    return list(result.nlargest(k).index)


if __name__ == "__main__":
    # ------------- data -------------
    # data = process_data.getScoreboard(DATA_FILE)
    data = None
    # ------------- user score -------------
    user_score = pd.DataFrame([[5, 6, 4, 8, 5, 8, None, 6, 7, 8, 5, 9]], index=[3],
    columns=['FLF2101', 'MAT1093', 'INT2204', 'INT1003', 'PHI1004', 'FLF2101', 'MAT1041', 'INT2203', 'INT1006', 'FLF2102', 'INT2207', 'PHY1100'])


    # ------------- Model -------------
    model = CF_UB(knn=None, nor='row_avg', sim='cosine')
    model.fit(data)

    # ------------- GreatestScoreCR -------------
    print(greatest_scoreCR(user_score, model, k=10))

    # ------------- SimilarNeighborCR -------------
    print(similar_neighborCR(user_score, model, k=10))
