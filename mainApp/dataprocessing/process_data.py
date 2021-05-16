import re
import os
import math
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore")

# public variable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_FOLDER = ROOT+"/data/raw_data"
CLEAR_FOLDER = ROOT+"/data/input/data"
SEMESTER_COURSE_FILE = ROOT+"/data/input/semester_courses.txt"
COURSE_INFO_FILE = ROOT+"/data/input/course_info.csv"


class DataExtraction:
    def __init__(self):
        self.student_info = None
        self.student_score = None
        self.course_list = None
        self.courses = None
        self.transcript = None

    def loadData(self, input_path: str):
        # print("loading: ", input_path)
        raw_data = pd.read_html(input_path)
        cols = list(raw_data[0].columns)
        # WARNNING: student info
        self.student_info = raw_data[0][4:-2][cols[1:5]].copy()
        self.student_info.columns = ['MSSV', 'name', 'gender', 'birth']
        #
        self.student_score = raw_data[0][4:-2][cols[1:2] + cols[5:-4]].copy()
        self.course_list = np.concatenate(
            (raw_data[1][0], raw_data[1][5][raw_data[1][5].notnull()]))  # đưa dữ liệu courses thành list
        # print("load ok")

    def getCourse(self):
        if self.courses is None:
            course_info = list()
            # Tách riêng dữ liệu cần sử dụng ra từ string sd thư viện re
            # cấu trúc stt_mmh: STC(stc)_tên:tmh, vd: 2_PHY1100:  STC(3)_Tên:Cơ - Nhiệt
            for mh in self.course_list:
                stt = int(re.findall("\d{1,2}", mh)[0])
                mmh = re.findall("[A-Z]+\s*\d+", mh)[0].replace(' ', '')
                stc = re.findall("\(\d{1,2}\)", mh)[0][1: -1]
                tmh = re.findall(":\S.*", mh)[0][1:]
                course_info.append([stt, mmh, tmh, stc])
            course_df = pd.DataFrame(course_info, columns=["stt", "MaMH", "TenMH", "TC"])
            self.courses = course_df.set_index("stt", drop=True).sort_index()

        return self.courses.copy()

    def getTranscript(self):
        if self.transcript is None:
            self.transcript = self.student_score
            self.transcript.columns = ["MSSV"] + list(self.getCourse()["MaMH"])
            # đăt lại kiểu cho dữ liệu
            self.transcript["MSSV"] = self.transcript["MSSV"].astype('str')
            self.transcript[list(self.getCourse()["MaMH"])] = self.transcript[list(self.getCourse()["MaMH"])].astype(
                'float')

            self.transcript.set_index("MSSV", drop=True, inplace=True)
            self.student_scores = self.transcript

        return self.transcript.copy()

    def getStudentInfo(self):
        return self.student_info.set_index("MSSV", drop=True)


if __name__ == '__main__':
    batches = os.listdir(RAW_FOLDER)
    batches.sort()

    extractor = DataExtraction()
    # get semester -> course to list
    cou_in_sem = list()
    with open(SEMESTER_COURSE_FILE, 'r') as sem_cour_file:
        for line in sem_cour_file:
            cou_arr = line.strip().split(", ")
            cou_in_sem.append(set(cou_arr))
        sem_cour_file.close()
    

    course_info = pd.DataFrame()
    try:
        course_info = pd.read_csv(COURSE_INFO_FILE)
    except:
        pass

    for batch in batches:
        print(batch)
        score_df = pd.DataFrame()
        class_names = os.listdir(RAW_FOLDER + "/" + batch)
        class_names.sort()
        semesters = os.listdir(RAW_FOLDER + "/" + batch + "/" + class_names[0])
        semesters.sort()
        # array of index of file name follow the order
        semester_index_sort = [(int(i/2) if i%2 == 0 else math.ceil((len(semesters)+i-1)/2)) for i in range(len(semesters))]
        semesters = [semesters[i] for i in semester_index_sort]
        del semester_index_sort

        for sem_index, sem_file_name in enumerate(semesters):
            print(str(sem_index) + " - " +sem_file_name)
            semester_df = pd.DataFrame()
            for class_name in class_names:
                extractor.__init__()
                extractor.loadData(RAW_FOLDER+"/"+batch+"/"+class_name+"/"+sem_file_name)
                # hợp danh sách sinh viên các lớp trong 1 kỳ
                semester_df = semester_df.append(extractor.getTranscript())
                course_info = course_info.append(extractor.getCourse(),ignore_index=True)
                course_info = course_info.drop_duplicates(subset=["MaMH"]).sort_values('MaMH')

            # Lấy danh sách các môn có trong một kỳ học
            if (len(cou_in_sem) <= sem_index):
                cou_in_sem.append(set(semester_df.columns))
            else:
                cou_in_sem[sem_index] = cou_in_sem[sem_index]|set(semester_df.columns)

            repeat_courses = list(set(semester_df.columns) & set(score_df.columns))  # lớp học(cột) bị lặp lại

            # lấy dữ liệu điểm số đầu tiên khác NaN
            for rc in repeat_courses:
                old_nan_i = score_df[score_df[rc].isnull()].index  # index sinh viên chưa có điểm môn này trong các kỳ trước
                new_sc_i = semester_df[semester_df[rc].notnull()].index  # index sinh viên có điểm môn này trong kỳ này
                first_sc_i = list(set(old_nan_i) & set(new_sc_i))  # index của sinh viên học lần đầu môn này

                score_df.loc[first_sc_i, rc] = semester_df.loc[first_sc_i, rc]  # gán giá trị
                semester_df.drop(rc, axis=1, inplace=True)  # xóa cột thừa (vì điểm đã đc nhập vào score_df)

            score_df = pd.concat([score_df, semester_df], axis=1, sort=False)

        # Ghi file data theo đúng dạng
        
        score_df.to_csv(CLEAR_FOLDER+"/"+batch+"_data.csv", index=False)
    # Ghi thông tin của các lớp học ra file
    course_info.to_csv(COURSE_INFO_FILE, index=False)

    # ghi file sem_cour_file
    with open(SEMESTER_COURSE_FILE, 'w') as sem_cour_file:
        for line in cou_in_sem:
            sem_cour_file.write(", ".join(line) + '\n')
        sem_cour_file.close()








