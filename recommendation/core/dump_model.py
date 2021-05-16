# add sys.path to run separation or with project
import sys
import os

module_path = os.path.abspath(os.getcwd())
if module_path not in sys.path:
    sys.path.append(module_path)

import psycopg2
import json
import pickle
from recommendation.core.CollaborativeFiltering import CollaborativeFiltering_IB, CollaborativeFiltering_UB
from recommendation.core.CollaborativeFiltering import CollaborativeFiltering_IB, CollaborativeFiltering_IB
from recommendation.core.MatrixFactorization import MatrixFactorization
from project import settings

# DATA_FILE = ['K60_data.csv']  # ['K60_data.csv', 'K61.csv']
DATABASE = settings.DATABASES['default']
MODEL_TABLE = 'mainApp_dumpmodel'


class DumpModelManager:
    conn = None

    def connect(self):
        DB = settings.DATABASES['default']
        try:
            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            self.conn = psycopg2.connect(host=DB.get('HOST') if DB.get('HOST') is None else 'localhost',
                                    database=DB['NAME'],
                                    user=DB['USER'],
                                    password=DB['PASSWORD'])
            print('Connect successful')
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        return self.conn

    def disconnect(self):
        if self.conn is not None and self.conn.closed == 0:
            self.conn.close()
        return self.conn

    def __del__(self):
        self.disconnect()

    def filter(self, dumpFile=None):
        if self.conn is None or self.conn.closed == 1:
            self.connect()
        cursor = self.conn.cursor()
        try:
            query = 'SELECT * FROM "mainApp_dumpmodel"'
            if dumpFile is not None and isinstance(dumpFile, str):
                query += ' WHERE "dumpFile" = \'{}\''.format(dumpFile)
            cursor.execute(query)
            records = cursor.fetchall()
        except Exception as e:
            cursor.close()
            print(e)
            return False

        cursor.close()
        return records

    def delete(self, dumpModelID=None, dumpFile=None):
        if dumpModelID is None and dumpFile is None:
            return 0

        if self.conn is None or self.conn.closed == 1:
            self.connect()
        cursor = self.conn.cursor()
        try:
            query = 'DELETE FROM "mainApp_dumpmodel"'
            if dumpModelID is None and dumpFile is not None:
                query += ' WHERE "dumpFile" = \'{}\';'.format(dumpFile)
            else:
                query += ' WHERE "dumpModelID" = {};'.format(dumpModelID)
            cursor.execute(query)
            rows_deleted = cursor.rowcount

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            print(e)
            return 0

        cursor.close()
        self.conn.commit()
        return rows_deleted

    def create(self, dumpFile, modelName, param="", args=""):
        if self.conn is None or self.conn.closed == 1:
            self.connect()
        cursor = self.conn.cursor()
        try:
            query = 'INSERT INTO "mainApp_dumpmodel"("dumpFile", "modelName", "param", "args", "updateTime", "active") VALUES (\'{}\', \'{}\', \'{}\', \'{}\', current_timestamp, FALSE);'.format(dumpFile, modelName, param, args)
            cursor.execute(query)
            row_created = cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            print(e)
            return 0

        cursor.close()
        self.conn.commit()
        return row_created

    def update(self, dumpModelID, update_dumpFile=None, update_modelName=None, update_param=None, update_args=None):
        if self.conn is None or self.conn.closed == 1:
            self.connect()
        cursor = self.conn.cursor()

        updates = []

        if update_dumpFile is not None:
            updates.append({"dumpFile": update_dumpFile})
        if update_modelName is not None:
            updates.append({"modelName": update_modelName})
        if update_param is not None:
            updates.append({"param": update_param})
        if update_args is not None:
            updates.append({"args": update_args})
        # print(updates)
        if len(updates) < 1:
            return 0

        try:
            query = 'UPDATE "mainApp_dumpmodel" SET'
            k, v = list(updates[0].items())[0]
            query += ' "{}" = \'{}\''.format(k, v)

            for d in updates[1:]:
                k, v = list(d.items())[0]
                query += ', "{}" = \'{}\''.format(k, v)

            query += ' WHERE "dumpModelID" = {};'.format(dumpModelID)
            # print(query)

            cursor.execute(query)
            
            row_updated = cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            print(e)
            return 0

        cursor.close()
        self.conn.commit()
        return row_updated

    def get_or_create(self, dumpFile, modelName="", param="", args=""):
        records = self.filter(dumpFile)
        created = False
        if len(records) < 1:
            row_created = self.create(dumpFile, modelName, param, args)
            created = row_created == 1
            records = self.filter(dumpFile)

        return records[0], created

    def update_or_create(self, dumpFile, update_modelName=None, update_param=None, update_args=None):
        records = self.filter(dumpFile)
        created = False
        if len(records) < 1:
            if update_param is None:
                update_param = ""

            row_created = self.create(dumpFile, update_modelName, update_param, update_args)
            created = row_created == 1
        else:
            id = records[0][0]
            row_updated = self.update(id, update_modelName=update_modelName, update_param=update_param, update_args=update_args)
            if row_updated < 1:
                print("Update error")

        records = self.filter(dumpFile)
        return records[0], created


def dumping(model_dict):
    dump_model_manager = DumpModelManager()
    dump_model_manager.connect()
    print("Storage folder root: ", settings.DUMPED_MODEL_ROOT)

    for key, model in model_dict.items():
        file_name = key + ".pickle"
        model_name = model['model'].__class__.__name__
        print("Model name:", model_name)
        path = settings.DUMPED_MODEL_ROOT + '/' + file_name
        try:
            with open(path, 'wb') as file:
                pickle.dump(model['model'], file)
                record, created = dump_model_manager.update_or_create(dumpFile=file_name, update_modelName=model_name,
                                                                      update_param=model['param'], update_args=model['args'])
                print("created" if created else "updated", " successful\n")
        except Exception as e:
            print(e)
            return None, 0

    dump_model_manager.disconnect()


if __name__ == '__main__':
    dump = DumpModelManager()

    # ------------------------------- WRITING MODEL HERE -------------------------------
    model_dict = {}
    # packing user base CF
    CF_UB = CollaborativeFiltering_UB(knn=10, nor='row_avg', sim='cosine')
    # CF_UB.fit(data)
    model_dict["CF_UB"] = {"model": CF_UB,
                           "param": json.dumps(CF_UB.param),
                           "args": '{"knn":10, "nor":"row_avg", "sim":"cosine"}'
                           }

    # packing item base CF
    CF_IB = CollaborativeFiltering_IB(knn=5, nor='col_avg', sim='cosine')
    # CF_IB.fit(data)
    model_dict["CF_IB"] = {"model": CF_IB,
                           "param": json.dumps(CF_IB.param),
                           "args": '{"knn":5, "nor":"col_avg", "sim":"cosine"}'
                           }

    # packing MF
    MF = MatrixFactorization(k=3, lamda=0.1, learning_rate=0.5, max_iteration=100)
    # MF.fit(data, random_state=0, scale=0.5)
    model_dict["MF"] = {"model": MF,
                        "param": json.dumps(MF.param),
                        "args": '{"k":5, "lamda":0.1, "learning_rate":0.5, "max_iteration":100}'
                        }

    # ------------------------------- END -------------------------------
    # dumping model
    dumping(model_dict)
