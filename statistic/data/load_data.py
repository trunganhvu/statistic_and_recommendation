import os
import json
from pandas import DataFrame, read_csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAR_FOLDER = ROOT+"/data/input/data"
SEMESTER_COURSE_JSON = ROOT+"/data/input/semester_courses.json"


def getSemesterCourses(semesters: list):
    if type(semesters) is not list and semesters != 'all':
        print("semesters type must be list or 'all' for all semesters")
        return None

    sem_course = json.load(open(SEMESTER_COURSE_JSON, 'r', encoding='utf-8'))

    if semesters == 'all':
        semesters = sem_course.keys()

    result = list()
    for sem in semesters:
        result += sem_course.get(str(sem))

    result = list(set(result))
    return result


def getListScoreboardFile():
    batches = os.listdir(CLEAR_FOLDER)
    batches.sort()
    return batches


def getScoreboard(batches: list = None):
    if type(batches) != type([]):
        batches = os.listdir(CLEAR_FOLDER)
        batches.sort()

    scoreboard = DataFrame()
    for batch in batches:
        # print(CLEAR_FOLDER+'/'+batch)
        scoreboard = scoreboard.append(read_csv(CLEAR_FOLDER + '/' + batch))

    scoreboard.reset_index(drop=True, inplace=True)
    return scoreboard
