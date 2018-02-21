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
from copy import copy

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
    def createAnalysis(repoID, data, rowCount, headers, reader):
        # TODO Analysis Steps
        # 1) Get Basic Column Info
        # 2) Check if column names already exist in a schema related to this repo
        # 3) Analyze data in a column and get type guess
        # 4) Return statistics about each column depending on type
        # 5) Format stats in a way that can be visualized
        #if 'JSON' in reader:
        #    return 0, 0, 0, -1
        frame = pd.DataFrame(data)
        columnCount, columns = AnalyzerManager.getColumns(frame)
        statistics = AnalyzerManager.getColumnStats(columns, frame, rowCount)
        statistics = AnalyzerManager.getColumnTypes(columns, frame, statistics)
        bestSchemaID = AnalyzerManager.getBestSchema(repoID, columns, frame, statistics, headers)
        return columnCount, columns, statistics, bestSchemaID

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
            # Gets rid of empty strings so that pandas doesn't analyze them
            col = frame[column].apply(lambda x: np.nan if isinstance(x, basestring) and (x.isspace() or x == "") else x)
            #try:
            #    stats = col.describe().to_dict() # Cast the returned panda Series to a dict
            #    valueFrequency = col.value_counts()
            #except TypeError:
            stats = col.astype(str).describe().to_dict()
            valueFrequency = col.astype(str).value_counts()
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
            dataTypes[p.name] = 0
        for column in columns:
            colTypes = copy(dataTypes)
            colList = frame[column].tolist()
            tmpPlugin = None
            for cell in colList:
                if cell is None or cell == '':
                    continue
                if tmpPlugin:
                    if tmpPlugin.validate(cell) is True:
                        colTypes[tmpPlugin.name] += 1
                        continue
                for plugin in dataTypePlugins:
                    if plugin.validate(cell) is True:
                        colTypes[plugin.name] += 1
                        break
                if tmpPlugin is None:
                    tmpPlugin = plugin
                elif colTypes[plugin.name] > colTypes[tmpPlugin.name]:
                    tmpPlugin = plugin
            sortedTypes = sorted(colTypes.items(), key=operator.itemgetter(1), reverse=True)
            dataType = sortedTypes[0][0]
            stats[column]['type'] = dataType
        return stats

    #
    # Find Best Schema Match
    # Or Recommend to create new schema if none match
    #
    @staticmethod
    def getBestSchema(repoID, columns, frame, stats, headers):
        colCount = len(headers)
        headers = [head.replace(' ', '_').lower() for head in headers]
        fieldMatches = 0
        for schema in SchemaManager.getTypes(repoID):
            schemaInfo = SchemaManager.getInfoForType(repoID, schema['id'])
            schemaFields = schemaInfo['fields']
            for field in schemaFields:
                if field['code'] in headers:
                    fieldMatches += 1
            if fieldMatches >= int(colCount * 0.9):
                return {"id": schema['id'], "name": schema["name"]}
        return False
