ROOT = ''
import numpy as np
import pandas as pd

# bar_point_abc = {'A': 8.5,
#              'B': 7.0,
#              'C': 5.5,
#              'D': 4.0,
#              'F': 0.0,
#              }
#
# bar_point_10 = {str(i): i for i in np.arange(1, 11, 1)}
#
# bar_point_20 = {str(i): i for i in np.arange(0.5, 10.5, 0.5)}


def distribute(data, boundary_array: list):
    dist = [data.shape[0]]

    boundary_array.sort()
    for boundary in boundary_array[1:]:
        data = data[data > boundary]
        t = len(data)
        dist[-1] -= t
        dist.append(t)

    return dist


def distribute_and_statistic(data, boundary_array: list, quantile_list=[0.25, 0.5, 0.75]):
    """
    :param data: np.ndarray, pd.DataFrame, pd.Series dữ liệu
    :param boundary_array: ranh giới
    :param quantile_list:
    :return: distribute, statistic
    distribute = [] same length with boundary_array
    statistic = [avg, min, q1, q2, q3, max]
    """
    if type(data) not in [list, np.ndarray, pd.DataFrame, pd.Series]:
        print("data type must be one of (list, np.ndarray, pd.DataFrame, pd.Series)")
        return None
    else:
        data = np.array(data)

    data = data.reshape((-1))
    data = data[~np.isnan(data)]
    dist = distribute(data, boundary_array)
    if len(data) <= 0:
        statistic = [None]*6
    else:
        q1, q2, q3 = np.quantile(data, quantile_list)
        min = np.min(data)
        avg = np.mean(data)
        max = np.max(data)
        statistic = [avg, min, q1, q2, q3, max]
    return dist, statistic


# def student_statistic(data, course_info=ROOT+'data/input/course_info.csv', save_to=ROOT+'data/result/student_statistic.csv'):
#     """ thống kê điểm của môi môn học
#     """
#     if type(data) is str:
#         data = pd.read_csv(open(data, 'r', encoding='utf-8'))
#
#     if type(course_info) is str:
#         course_info = pd.read_csv(open(course_info, 'r', encoding='utf-8'), index_col='MaMH')
#
#     course_credit = course_info.loc[data.columns, 'TC'].values
#
#     data = data*course_credit  # điểm nhân tín chỉ
#
#     stu_sta = pd.DataFrame(columns=['ID', 'No. course', 'Credits', 'GPA'])
#     for i, row in data.iterrows():
#         cols = row.dropna().index  # các môn sinh viên học
#         total_courses = course_info.loc[cols, 'TC']
#
#         stu_sta = stu_sta.append({'ID' : i,
#             'No. course': total_courses.count(),
#             'Credits' : total_courses.sum(),
#             'GPA' : row.sum() / total_courses.sum()
#             },
#             ignore_index=True)
#
#     stu_sta[['ID', 'No. course', 'Credits']] = stu_sta[['ID', 'No. course', 'Credits']].astype(int)
#
#     if save_to is not None:
#         stu_sta.to_csv(save_to, index=False, encoding='utf-8')
#
#     # visual data
#     plot_data = stu_sta['No. course']
#
#     fig, ax = plt.subplots(1)  # sharex=True, sharey=True
#     fig.set_figheight(7)
#     fig.set_figwidth(10)
#     mean = plot_data.mean()
#     std = sta.stdev(list(plot_data.dropna().T))
#
#     ax = sns.distplot(plot_data.values, bins=20)
#     ax.set_xticks(range(0, 60, 5))
#
#     print("min: {}".format(plot_data.min()))
#     print("max: {}".format(plot_data.max()))
#     print("mean: {}".format(mean))
#     print("std: {}".format(std))
#
#     qs = plot_data.quantile([0.25,0.5,0.75])
#     print(qs)
#
#     ylim = ax.get_ylim()
#     ax.plot([mean, mean], ylim, color='orange')
#     ax.plot([mean + std, mean + std], ylim, color='y')
#     ax.plot([mean - std, mean - std], ylim, color='y')
#     ax.yaxis.grid(True, linestyle=':', linewidth=0.5)
#     # ax.set_title(col)
#
#     th = 0
#     for p in ax.patches:
#         th += p.get_height()
#
#     x = np.count_nonzero(~np.isnan(plot_data))/th
#
#     for p in ax.patches:
#         ax.text(p.get_x() + p.get_width() / 2,
#                 p.get_height(),
#                 str(int(round(p.get_height() * x))),
#                 color = 'blue',
#                 # fontsize=10,
#                 ha='center',
#                 va='bottom')
#     plt.show()
#
#     return stu_sta

# def score_histogram(data, col=None):
#     """ vẽ sơ đồ mật độ điểm của môn học
#     """
#     if type(data) is str:
#         data = pd.read_csv(open(data, 'r', encoding='utf-8'))
#
#     if col is None:
#         col = data.columns[0]
#
#     fig, ax = plt.subplots(1)  # sharex=True, sharey=True
#     fig.set_figheight(7)
#     fig.set_figwidth(10)
#     plot_data = data[col]
#     mean = plot_data.mean()
#     std = sta.stdev(list(plot_data.dropna().T))
#
#     ax = sns.distplot(plot_data, bins=20)
#     ax.set_xticks(range(11))
#
#     ylim = ax.get_ylim()
#     ax.plot([mean, mean], ylim, color='orange')
#     ax.plot([mean + std, mean + std], ylim, color='y')
#     ax.plot([mean - std, mean - std], ylim, color='y')
#     ax.yaxis.grid(True, linestyle=':', linewidth=0.5)
#     ax.set_title(col)
#
#     th = 0
#     for p in ax.patches:
#         th += p.get_height()
#
#     x = np.count_nonzero(~np.isnan(plot_data))/th
#
#     for p in ax.patches:
#         ax.text(p.get_x() + p.get_width()/2.,
#                 p.get_height(),
#                 str(int(round(p.get_height() * x))),
#                 color = 'blue',
#                 # fontsize=10,
#                 ha='center',
#                 va='bottom')
#
#     plt.show()

# def summary_histogram(data):
#     if type(data) is str:
#         data = pd.read_csv(open(data, 'r', encoding='utf-8'))
#
#     scores = data.values.reshape(-1)
#     scores = scores[~np.isnan(scores)]
#     mean = scores.mean()
#     std = sta.stdev(scores)
#
#     fig, ax = plt.subplots(1)  # sharex=True, sharey=True
#
#     ax = sns.distplot(scores, bins=20)
#     ax.set_xticks(range(11))
#     fig.set_figheight(7)
#     fig.set_figwidth(10)
#     ylim = ax.get_ylim()
#
#
#     ax.plot([mean, mean], ylim, color='orange')
#     ax.plot([mean + std, mean + std], ylim, color='y')
#     ax.plot([mean - std, mean - std], ylim, color='y')
#     ax.yaxis.grid(True, linestyle=':', linewidth=0.5)
#     print(mean, std)
#     # ax.legend(['Density', ])
#
#     th = 0
#     for p in ax.patches:
#         th += p.get_height()
#
#     x = np.count_nonzero(~np.isnan(plot_data))/th
#
#     for p in ax.patches:
#         ax.text(p.get_x() + p.get_width()/2.,
#                 p.get_height(),
#                 str(int(round(p.get_height() * x))),
#                 color='blue',
#                 # fontsize=14,
#                 ha='center',
#                 va='bottom')
#     plt.show()

# def letter_grade_bar(statistic):
#     if type(statistic) is str:
#         statistic = pd.read_csv(open(statistic, 'r', encoding='utf-8'))
#
#     data = statistic[['A','B','C','D','F']].sum()
#     print(data)
#     fig, ax = plt.subplots(1)  # sharex=True, sharey=True
#     ax.bar(data.index, data, width=.5)
#
#     for p in ax.patches:
#         ax.text(p.get_x() + p.get_width()/2.,
#                 p.get_height(),
#                 str(p.get_height()),
#                 color='gray',
#                 # fontsize=14,
#                 ha='center',
#                 va='bottom')
#
#     plt.show()



if __name__ == "__main__":
    # SAVE_PATH = 'data/result/grade_statistic.csv'
    # k60 = pd.read_csv("data/input/data/K60_data.csv")
    # k61 = pd.read_csv('data/input/data/K61.csv')
    # df = pd.concat([k60, k61], ignore_index=True)
    # score_histogram(df, 'MAT1093')
    # print(student_statistic('data/input/data/K60_data.csv'))
    # print(grade_statistic('data/input/data/K60_data.csv', save_to=SAVE_PATH))
    # print(df['INT3306'].count())
    # summary_histogram(k61)
    # letter_grade_bar('data/result/grade_statistic.csv')

    data = np.array([[1, 2, 3, 1, 4, 2, 4, 1],
                     [3, 2, 5, 3, 3, 4, 2, 1],
                     ])

    print(distribute(data, [0, 1, 2, 3, 4]))

    """[[3 1]
 [2 2]
 [1 3]
 [2 1]
 [0 1]]

"""