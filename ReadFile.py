import json
import csv
import os
import pandas as pd


class File(object):
    def __init__(self, fp):
        _path, _ext = os.path.splitext(fp)
        self.fp = fp
        self.path = _path
        self.filename = _path.split("/")[-1]
        self.ext = _ext


class CsvFile(File):
    def __init__(self, fp):
        super().__init__(fp)

    def read(self):
        return pd.read_csv(self.fp)

    def write(self, data):
        data.to_csv(self.fp, encoding="utf_8_sig", index=False)


class JsonFile(File):
    def __init__(self, fp):
        super().__init__(fp)

    def read(self):
        f = open(self.fp, "r", encoding="utf-8")
        result = json.load(f)
        f.close()
        return result

    def write(self, data):
        #:HACK
        pass
