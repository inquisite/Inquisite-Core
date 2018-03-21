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
from lib.managers.ListManager import ListManager
from api.sockets.socket_resp import pass_message
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
        col_clean = {}
        for col in columns:
            if isinstance(col, str):
                col_clean[col] = unicode(col, errors="ignore")
                continue
            col_clean[col] = col
        frame.rename(index=str, columns=col_clean)
        pass_message('upload_step', {"step": "Column Statistics", "pos": 40})
        pass_message('upload_status', {"status": "Getting stats for columns", "pos": 0})
        statistics = AnalyzerManager.getColumnStats(columns, frame, rowCount, columnCount)
        pass_message('upload_status', {"status": "Getting column types", "pos": 0})
        statistics = AnalyzerManager.getColumnTypes(columns, frame, statistics, columnCount)
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
    def getColumnStats(columns, frame, rowCount, colCount):
        statistics = {}
        colNo = 1
        for column in columns:
            if isinstance(column, str):
                disp_column = unicode(column, errors="ignore")
            else:
                disp_column = str(column)
            data_pos = round((float(colNo)/colCount)*100)
            pass_message('upload_status', {"status": "Getting stats for column " + disp_column, "pos": data_pos})
            # Gets rid of empty strings so that pandas doesn't analyze them
            col = frame[column].apply(lambda x: np.nan if isinstance(x, basestring) and (x.isspace() or x == "") else x)

            stats = col.astype('unicode').describe().to_dict()
            valueFrequency = col.astype('unicode').value_counts()
            highFreqValues = valueFrequency.iloc[0:3].to_dict()
            sortedValues = sorted(highFreqValues.items(), key=operator.itemgetter(1), reverse=True)
            statistics[disp_column] = {
                "Total Values": stats['count'],
                "Unique Values": stats['unique'],
                "Null Values": rowCount - stats['count'],
                "frequent_values": sortedValues,
                "type": None,
                "value_array": valueFrequency.to_json()
            }
            colNo += 1
        return statistics

    #
    # Generate column types
    #
    @staticmethod
    def getColumnTypes(columns, frame, stats, colCount):
        dataTypes = {}
        dataType = 'String'
        dataTypePlugins = []
        colStep = 70/colCount
        col_pos = 30 + colStep
        for x in SchemaManager.getDataTypes():
            p = SchemaManager.getDataTypeInstance(x)
            dataTypePlugins.append(p)
            dataTypes[p.name] = 0
        for column in columns:
            if isinstance(column, str):
                disp_column = unicode(column, errors="ignore")
            else:
                disp_column = str(column)
            pass_message('upload_step', {"step": "Getting type of column " + disp_column, "pos": col_pos})
            colTypes = copy(dataTypes)
            colList = frame[column].tolist()
            tmpPlugin = None
            cell_total = len(colList)
            cell_chunk = int(cell_total/100)
            if cell_chunk == 0:
                cell_chunk = 1
            cell_count = 1
            chunk_count = 1
            if cell_chunk == 1:
                chunk_count = 100/cell_total
            chunk_display = chunk_count
            for cell in colList:
                cell_count += 1
                if cell_count % cell_chunk == 0:
                    status_str = "Analyzing type of cells " + str(cell_count) + "-" + str(cell_count+cell_chunk)
                    pass_message('upload_status', {"status": status_str, "pos": int(chunk_display)})
                    chunk_display += chunk_count
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
            # If this is text, check to see if it can be considered a list
            if dataType == 'Text':
                listTest = set(colList)
                uCount = ListManager.uniqueValueCount(listTest)
                if uCount:
                    if colCount*0.2 > uCount:
                        stats[disp_column]['type'] = 'List'
                        col_pos += colStep
                        continue
            stats[disp_column]['type'] = dataType
            col_pos += colStep
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
