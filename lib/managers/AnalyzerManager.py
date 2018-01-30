import time
import datetime
from lib.utils.Db import db
import datetime
import time
import re
import json
import operator
import pandas as pd
import numpy as np

from lib.utils.Db import db
from lib.exceptions.ValidationError import ValidationError
from lib.exceptions.DbError import DbError
from lib.exceptions.FindError import FindError
from pluginbase import PluginBase
from lib.decorators.Memoize import memoized
from lib.managers.SchemaManager import SchemaManager

class AnalyzerManager:


    #
    # Manage the analysis process
    #
    @staticmethod
    def createAnalysis(data, rowCount):
        # TODO Analysis Steps
        # 1) Get Basic Column Info
        # 2) Check if column names already exist in a schema related to this repo
        # 3) Analyze data in a column and get type guess
        # 4) Return statistics about each column depending on type
        # 5) Format stats in a way that can be visualized
        frame = pd.DataFrame(data)
        columnCount, columns = AnalyzerManager.getColumns(frame)
        statistics = AnalyzerManager.getColumnStats(columns, frame, rowCount)
        statistics = AnalyzerManager.getColumnTypes(columns, frame, statistics)
        return columnCount, columns, statistics

    #
    # Get columns from DataFrame
    #
    @staticmethod
    def getColumns(frame):
        cols = frame.keys()
        colCount = len(cols)
        return colCount, cols

    #
    # Generate basic statistics for each column
    #
    @staticmethod
    def getColumnStats(columns, frame, rowCount):
        statistics = {}
        for column in columns:
            col = frame[column].replace('', np.nan) # Gets rid of empty strings so that pandas doesn't analyze them
            stats = col.describe().to_dict() # Cast the returned panda Series to a dict
            valueFrequency = col.value_counts()
            highFreqValues = valueFrequency.iloc[0:3].to_dict()
            sortedValues = sorted(highFreqValues.items(), key=operator.itemgetter(1), reverse=True)
            statistics[column] = {
                "Total Values": stats['count'],
                "Unique Values": stats['unique'],
                "Null Values": rowCount - stats['count'],
                "frequent_values": sortedValues,
                "type": None,
                "value_array": valueFrequency.to_json()
            }
        return statistics

    #
    # Generate column types
    #
    @staticmethod
    def getColumnTypes(columns, frame, stats):
        dataTypes = {}
        dataType = 'String'
        dataTypePlugins = []
        for x in SchemaManager.getDataTypes():
            p = SchemaManager.getDataTypeInstance(x)
            dataTypePlugins.append(p)
        for column in columns:
            colTypes = {'Integer': 0, 'Float': 0, 'Text': 0, 'Date range': 0, 'Georeference': 0}
            colList = frame[column].tolist()
            tmpPlugin = None
            for cell in colList:
                if tmpPlugin:
                    if tmpPlugin.validate(cell):
                        colTypes[tmpPlugin.name] += 1
                        continue
                for plugin in dataTypePlugins:
                    if plugin.validate(cell):
                        colTypes[plugin.name] += 1
                        break
                tmpPlugin = plugin

            sortedTypes = sorted(colTypes.items(), key=operator.itemgetter(1), reverse=True)
            if sortedTypes[0][1] > (sortedTypes[1][1] * 9):
                dataType = sortedTypes[0][0]
            stats[column]['type'] = dataType

        return stats