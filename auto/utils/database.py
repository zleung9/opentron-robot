# -*- coding: utf-8 -*-

# Import packages
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, types
import warnings
warnings.simplefilter('ignore', np.RankWarning)


class Database():

    def __init__(self, db=None, username="zliang", pwd="Automat46305!"):
        self.username = username
        self.pwd = pwd
        self.engine = None
        self.name = None
        self.table = None
        if db is not None:
            self.connect(db)

    def connect(self, db: str):
        conn_string = f'mysql+mysqlconnector://{self.username}:{self.pwd}@192.168.1.91:3306/{db}'
        self.engine = create_engine(conn_string)
        self.name = db

    def disconnect(self):
        del self.name
        self.name = None

    def pull(self, table="", remove_index=True):
        """Pull data from a given table on database.
        """
        assert self.engine is not None
        engine = self.engine
        data = pd.read_sql_table(table, engine)
        if remove_index:
            data = self._remove_index(data)
        return data


    def push(self, data:pd.DataFrame=None, table:str="") -> None:
        """Push data to update a given table on database.
        Parameters
        ----------
        data : pandas.DataFrame

        """
        assert self.engine is not None
        engine = self.engine
        if table == "":
            print("No table is updated! Please specify a table name")
            return
        else:
            try:
                data.to_sql(
                    table, 
                    con=engine, 
                    if_exists='replace', 
                    index=True,
                    chunksize=100, # write 100 rows each time
                    dtype={'graph': types.LargeBinary(length=2000000)}
                )
            except Exception as e:
                print("Smoething went wrong")
                print(e)
            else:
                print(f"{table} successfully updated.")


    def _remove_index(self, data):
        _data = data.copy()
        if "index" in _data.columns:
            _data = _data.drop('index', axis=1)
        elif "id" in data.columns:
            _data = _data.drop('id', axis=1)
        return _data
    

if __name__ == "__main__":
    db = Database(db="test_db")
    df = db.pull(table="half_cell_classifier_test")