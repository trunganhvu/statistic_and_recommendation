import numpy as np
import pandas as pd
from .lib import process


class TrainMF:
    """ công thức cập nhập với Y = X . W
    X += learn_rate*(Y - X.dot(W)).dot(W.T)/2*num_learned_course + lam*X/(m*k))
    W += learn_rate*(X.T.dot(Y - X.dot(W)))/2*num_attended_student + lam*W/(n*k))
    Trên ma trận thì num_learned_course = num_attended_student, nhưng cập nhập với từng dòng/cọt thì nó lại khác
    Ta cập nhập ma trận theo từng dòng sử dụng learn_rate * đạo hàm và regularization (lam*X) để tránh overfitting
    """
    def __init__(self, k=5, lamda=0.1, learning_rate=0.5, train_menthod:str='inter_num', max_iteration=1000,
                 accepted_loss=0.01, negligible_change=0.0001, negligible_change_iter=5):
        self.k = k
        self.lam = lamda
        self.lr = learning_rate
        self.menthod = train_menthod
        # train_menthod in ['inter_num', 'accepted_loss', 'negligible_change']
        self.max_iter = max_iteration
        if self.menthod == 'accepted_loss':
            self.ac_loss = accepted_loss
        elif self.menthod == 'negligible_change':
            self.nlg_diff = negligible_change
            self.nlg_iter = negligible_change_iter
    
    def fit(self, data, row_feature, col_feature, nona_row, nona_col):
        self.Y = data
        self.X = row_feature
        self.W = col_feature
        self.nona_row = nona_row
        self.nona_col = nona_col

    def RMS_loss(self):
        """ calculate the loss of model follow root maen square formular
        """
        loss_matrix = self.Y - self.X.dot(self.W)
        loss = np.sqrt(
            np.nansum(loss_matrix*loss_matrix) 
            / np.count_nonzero(~np.isnan(loss_matrix))
            )
        return loss

    def loss(self):
        """ calculate the loss of model follow update menthod formular
        learn_rate*(Y - X.dot(W)).dot(W.T)/2*num_learned_course + lam*X/(2*m*k))
        """
        loss_matrix = self.Y - self.X.dot(self.W)
        main_loss = np.nansum(loss_matrix*loss_matrix) / np.count_nonzero(~np.isnan(loss_matrix))
        regularization = (self.lam/self.k)*(
            np.sqrt(np.sum(self.X*self.X)) +
            np.sqrt(np.sum(self.W*self.W))
            )
        loss = main_loss/2 + regularization/2
        return loss

    def update_X(self):
        """ Ta cập nhập theo từng dòng và bỏ qua các nan trong dòng để tránh lỗi khi nhân với ma trận loss có nan 
        """
        loss_matrix = self.Y - self.X.dot(self.W)
        for i in range(self.X.shape[0]):
            row = loss_matrix[i, self.nona_row[i]]
            CMF = self.W[:, self.nona_row[i]]  # chỉ lấy những ô có giá trị
            n_course = len(self.nona_row[i])
            self.X[i, :] += self.lr*(
                    row.dot(CMF.T)/n_course -
                    (self.lam/self.k)*self.X[i, :]
            )  # cập nhập

    def update_W(self):
        """ Ta cập nhập theo từng cột và bỏ qua các nan trong cột để tránh lỗi khi nhân với ma trận loss có nan
        """
        loss_matrix = self.Y - self.X.dot(self.W)
        for i in range(self.W.shape[1]):
            col = np.array([loss_matrix[self.nona_col[i], i]]).T
            UMF = self.X[self.nona_col[i], :]  # chỉ lấy ô có giá trị
            n_user = len(self.nona_col[i])
            self.W[:, [i]] += self.lr*(
                UMF.T.dot(col)/n_user - 
                (self.lam/self.k)*self.W[:, [i]]
                )  # cập nhập
    
    def iter_train(self):
        for i in range(self.max_iter):
            self.update_X()
            self.update_W()
        self.inter = i + 1

    def accepted_loss_train(self):
        """ Phương pháp huấn luyện này chạy cho đến khi mất mát nhỏ hơn hoặc bằng mức chập nhận được hoặc nó đã chạy hết số vòng lặp tối đa được thiết lập ban đầu.

        Ta sử dụng RMS_loss thay vì loss bởi vì hàm loss bị ảnh hưởng khi thay đổi giá trị lamda còn hàm 
        RMS_loss thì không bên cạnh đó RMS_loss thể hiện chính xác hơn sự sai khác của ma trận dự đoán so với 
        ma trận gốc. 
        """
        self.inter = 0
        while self.RMS_loss() > self.ac_loss and self.inter < self.max_iter:
            self.update_X()
            self.update_W()
            self.inter += 1
        
    def negligible_change_train(self):
        """ Phương pháp huấn luyện này chạy cho đến khi sự chênh lệch về mất mát giữa hai lần lặp nhỏ hơn hoặc bằng mức đã cài đặt hoặc nó đã chạy hết số vòng lặp tối đa được thiết lập ban đầu.
        
        Ta sử dụng loss bởi vì phương pháp cập nhập này phụ thuộc vào độ thay đổi của hàm cập nhập để xác định 
        điểm dừng nên ta phải sử dụng hàm mất mát đúng với đạo hàm dùng để cập nhập
        """
        self.inter = 0
        inter_in_nlg = 0
        old_loss = self.RMS_loss()
        while inter_in_nlg < self.nlg_iter and self.inter < self.max_iter:
            self.update_X()
            self.update_W()
            new_loss = self.RMS_loss()
            self.inter += 1
            if old_loss - new_loss < self.nlg_diff:
                inter_in_nlg += 1
            else:
                inter_in_nlg = 0
            old_loss = new_loss
                
    def train(self):
        if self.menthod == 'inter_num':
            self.iter_train()
        if self.menthod == 'accepted_loss':
            self.accepted_loss_train()
        elif self.menthod == 'negligible_change':
            self.negligible_change_train()
    
    def get_result_matrix(self):
        return self.X.dot(self.W)


class MatrixFactorization:
    """ Tạo ngẫu nhiên 2 ma trận user_MF và course_MF và huấn luyện sao cho data ~ user_MF . course_MF,
    rồi dựa và các matrix feature để dự đoán các ô trống

    Phương pháp này cần tính toán nhiều và hiệu suất cao, nên thay vì sử dụng DataFrame
    ta sẽ sử dụng numpy.array để tăng hiệu suất (nhanh hơn sấp xỉ 100)

    (ngày 15/02/2020) Tạm thời class này sẽ hướng tới dạng phiên bản mang tính thử nghiệm có thể chạy trên web
    nhưng hiệu suất của nó sẽ không cao (không thể chạy song song nhiều) thay vào đó tập trung vào dự đoán tron, mục đích là để tiết kiệm thời gian khi chạy và dễ dàng so sánh kết quả với 
    các mô hình khác
    """
    param = {
        'k': {
            'description': "Num of hidden feature cols",
            'type': 'int',
            'default': 3,
        },
        'lamda': {
            'description': "float in range(0, 1), lamda relate to update and loss",
            'type': 'float',
            'default': 0.1,
        },
        'learning_rate': {
            'description': "learning rate should < 1",
            'type': 'float',
            'default': 0.5,
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
        'standard_scale': {
            'description': "scale rate, range of grade should be scale to (0, 1)",
            'type': 'float',
            'default': 0.1,
        },
        'max_iteration': {
            'description': "number of iteration, the more iteration the slower the model",
            'type': 'int',
            'default': 100,
        }
    }

    def __init__(self, k=3, lamda=0.1, learning_rate=0.5, nor: str = 'row_avg', standard_scale: int = 0.1, max_iteration=100):
        # , train_menthod:str='inter_num', accepted_loss=0.01, negligible_change=0.0001, negligible_change_iter=10):
        """
        data = user_MF x course_MF  <=>  Y = X x W
        :param k: Num of hidden feature cols
        :param lamda: float in range(0, 1) làm hệ số ảnh hưởng của norm 2 X và W
        :param learning_rate:
        :param nor:
        """
        self.k = k
        self.lam = lamda
        self.lr = learning_rate
        self.nor_type = nor
        self.scale = standard_scale
        self.sd_data = None  # np.array([])
        self.courses = None  # list()
        self.learned_courses = None  # list()  # danh sách các môn đã học của sinh viên theo stt
        self.attended_students = None  # list()  # danh sách các sinh viên đã tham gia môn học theo stt
        self.max_iter = max_iteration
        # if train_menthod not in ['inter_num', 'accepted_loss', 'negligible_change']:
        #     self.menthod = 'inter_num'
        # else:
        #     self.menthod = train_menthod
        # self.ac_loss = accepted_loss,
        # self.nlg_diff = negligible_change
        # self.nlg_iter = negligible_change_iter
        
        # self.attributes = ['k', 'menthod', 'nor_type',
        # 'lr', 'lam', 'scale',
        # 'max_iter', 'ac_loss', 'nlg_diff', 'nlg_iter']
    
    def standardized(self, data: np.array):
        data_nor, data_avg = process.normalize(data, self.nor_type)
        scaled_data = self.scale*data_nor

        return scaled_data, data_avg

    def invert_standardized(self, data, data_avg):
        data_nor = data/self.scale
        result = data_nor + data_avg
        return result

    def get_learned_attended_list(self, data: np.array):
        """ Được sử dụng để xác định các sinh viên nào đã học một môn bất kỳ
        và các môn học đã được một sinh viên bất kỳ học.
        Danh sách chủ yếu làm giảm thời gian huấn luyện vì được dùng lại trong các vòng lặp huấn luyện
        Khi dự đoán không cần thiết lắm có thể xóa bỏ để giảm lượng không gian nhớ bị chiếm
        """
        learned_courses = []
        for i in range(data.shape[0]):
            nona_list = np.argwhere(~np.isnan(data[i, :]))
            learned_courses.append(list(np.concatenate(nona_list, axis=None)))
        
        attended_students = []
        for i in range(data.shape[1]):
            nona_list = np.argwhere(~np.isnan(data[:,i]))
            attended_students.append(list(np.concatenate(nona_list, axis=None)))
        return learned_courses, attended_students

    def fit(self, data: pd.DataFrame, user_MF=None, course_MF=None, random_state=None, loc:float=0, scale:float=0.5):
        """
        Ta sẽ nhập DataFrame vào nhưng sẽ chuyển đổi về np.array để dễ tính toán sau đó chuyển đổi lại sử dụng cột của data khi cần
        Ở đây ta sd random.normal để sd phân phối Gaussian (phân phối chuẩn) để hội tụ biến về gần 0 trung bình của điểm
        thang điểm 10 thì phương sai nên chọn là 2 hoắc nhỏ hơn để các ngẫu nhiên không ra quá xa
        :param data:
        :param semester_course:
        :param user_MF (user matrix feature):
        :param course_MF (course matrix feature):
        :param random_state:
        :param loc: 
        :param scale: scale nên < 0.5 bởi tính chất
        :return:
        """
        if type(data) == str:
            data = pd.read_csv(open(data, 'r', encoding='utf-8'))
        else:
            data = pd.DataFrame(data.copy())

        self.data = data

        # set random 
        np.random.seed(random_state)
        self.ran_loc = loc
        self.ran_scale = scale
        # required preprocess data to avoid error
        data = data.dropna(axis=1, thresh=10).dropna(axis=0, thresh=5)
        # columns
        self.courses = data.columns
        # standard data và avg
        self.sd_data, self.data_avg = self.standardized(np.array(data))
        # list of non nan position on data
        self.learned_courses, self.attended_students = self.get_learned_attended_list(self.sd_data)
        # check size of data vs self.k
        if min(self.sd_data.shape) < self.k:
            self.k = min(self.sd_data.shape)

        self.user_id = len(data)  # id của người dùng sẽ đc xếp cuối cùng sau khi nhập dữ liệu

        # check base of user_MF and course_MF inited and create random if necessary
        user_MF = np.array(user_MF)
        if user_MF.shape != (self.sd_data.shape[0], self.k):
            self.user_MF_base = np.random.normal(self.ran_loc, self.ran_scale, (self.sd_data.shape[0], self.k))
        else:
            self.user_MF_base = user_MF

        course_MF = np.array(course_MF)
        if course_MF.shape != (self.k, self.sd_data.shape[1]):
            self.course_MF_base = np.random.normal(self.ran_loc, self.ran_scale, (self.k, self.sd_data.shape[1]))
        else:
            self.course_MF_base = course_MF

    def predict(self, user_score: pd.DataFrame, course_need_pre: list = None):
        # check course_need_pre
        if course_need_pre is None or len(course_need_pre) < 1:
            course_need_pre = self.courses
        else:
            course_need_pre = set(course_need_pre)
            n = []
            for c in set(course_need_pre):
                if c in self.courses:
                    n.append(c)
            course_need_pre = n.copy()
            del n, c

        # courses learned and need pre
        cols = set(list(user_score.columns) + course_need_pre)

        course_need_pre = list(cols - set(user_score.columns))

        cols = list(cols)

        # train model
        MF_train = TrainMF(self.k, self.lam, self.lr, 
        self.menthod, self.max_iter, self.ac_loss, self.nlg_diff, self.nlg_iter)
        # standardized user data 
        user_id = user_score.index
        new_row = pd.DataFrame(user_score, columns=cols)
        new_row, user_avg = self.standardized(np.array(new_row))  # user_avg
        # update data to train_data
        train_data = np.array(np.concatenate([self.sd_data, new_row]))
        # update non na list 
        index = train_data.shape[0] - 1  # index
        user_nona = list(np.concatenate(np.argwhere(~np.isnan(new_row))))
        
        learned_courses = self.learned_courses.copy()
        if len(learned_courses) <= index:
            learned_courses.append(user_nona)
        else:
            learned_courses[index] = user_nona
        
        attended_students = self.attended_students.copy()
        for i in range(len(attended_students)):
            if i in user_nona:
                if index not in attended_students[i]:
                    attended_students[i].append(index)
            else:
                if index in attended_students[i]:
                    attended_students[i].remove(index)
        del user_nona, new_row
        # random new user feature
        new_row_feature = np.random.normal(self.ran_loc, self.ran_scale, (1, self.k))
        user_MF = np.concatenate([self.user_MF_base, new_row_feature])
        # fitting and train data
        MF_train.fit(train_data, user_MF, self.course_MF_base.copy(), learned_courses, attended_students)
        del user_MF, new_row_feature, learned_courses, attended_students
        MF_train.train()

        # get predicted score
        sd_pre_score = MF_train.get_result_matrix()[index]
        # re-format pre_score_nor
        pre_score = self.invert_standardized(sd_pre_score, user_avg)
        score = pd.DataFrame(pre_score, index=user_id, columns=cols)
        # Sửa lỗi điểm dự đoán
        return process.formal_score(score[course_need_pre])

