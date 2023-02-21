import csv
from collections import OrderedDict 
import matplotlib.pyplot as plt, matplotlib.font_manager as fm

class TimeSeriesData(object):
    def __init__(self, givenTimeSeriesDataAsDict, givenHeaderName):
        assert(isinstance(givenTimeSeriesDataAsDict, OrderedDict))
        self.__dataAsDict = givenTimeSeriesDataAsDict
        self.__headerName = givenHeaderName
    
    def getData(self):
        return self.__dataAsDict

    def getHeaderName(self):
        return self.__headerName
    
    def queryNumberOfElemens(self):
        numberOfElements = len(self.__dataAsDict)
        return numberOfElements
    
    def __peer_handled(self, givenTimeSeries): # if two objects can be handled by some operators such as 'timeSeries1 + timeSeries2'.
        assert(isinstance(givenTimeSeries, TimeSeriesData))
        firstKeys = self.get_data().keys()
        secondKeys = givenTimeSeries.get_data().keys()
        return firstKeys == secondKeys
    
    def __operator(self, givenTimeSeries, givenOperatorType):
        isAllowed = self.__peer_handled(givenTimeSeries)
        if isAllowed == False:
            raise TypeError('two time series cannot be handled in element-wise way!')
        dataAsDict = OrderedDict()
        for itemLeft, itemRight in self.get_data(), givenTimeSeries.get_data():
            time = itemLeft.keys()[0]
            if givenOperatorType == '+':
                value = itemLeft.values()[0] + itemRight.values()[0]
            if givenOperatorType == '-':
                value = itemLeft.values()[0] - itemRight.values()[0]
            if givenOperatorType == '*':
                value = itemLeft.values()[0] * itemRight.values()[0]
            if givenOperatorType == '/':
                value = itemLeft.values()[0] / (1.0 * itemRight.values()[0])
            dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData

    def __add__(self, givenObject):
        if isinstance(givenObject, TimeSeriesData) == True:
            dataAsDict = self.__operator(givenTimeSeries = givenObject, givenOperatorType = '+')
        else:
            dataAsDict = OrderedDict()
            for item in self.get_data().items():
                time = item[0]
                value = item[1] + givenObject
                dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData    
    
    def __sub__(self, givenObject):
        if isinstance(givenObject, TimeSeriesData) == True:
            dataAsDict = self.__operator(givenTimeSeries = givenObject, givenOperatorType = '-')
        else:
            dataAsDict = OrderedDict()
            for item in self.get_data().items():
                time = item[0]
                value = item[1] - givenObject
                dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData  

    def __mul__(self, givenObject):
        if isinstance(givenObject, TimeSeriesData) == True:
            dataAsDict = self.__operator(givenTimeSeries = givenObject, givenOperatorType = '*')
        else:
            dataAsDict = OrderedDict()
            for item in self.get_data().items():
                time = item[0]
                value = item[1] * givenObject
                dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData  
    
    def __truediv__(self, givenObject):
        if isinstance(givenObject, TimeSeriesData) == True:
            dataAsDict = self.__operator(givenTimeSeries = givenObject, givenOperatorType = '/')
        else:
            dataAsDict = OrderedDict()
            for item in self.get_data().items():
                time = item[0]
                value = item[1] / (1.0 * givenObject)
                dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData  

    def __radd__(self, givenNumber):
        dataAsDict = OrderedDict()
        for item in self.get_data().items():
            time = item[0]
            value = givenNumber + item[1]
            dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData   

    def __rsub__(self, givenNumber):
        dataAsDict = OrderedDict()
        for item in self.get_data().items():
            time = item[0]
            value = givenNumber - item[1]
            dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData   

    def __rmul__(self, givenNumber):
        dataAsDict = OrderedDict()
        for item in self.get_data().items():
            time = item[0]
            value = givenNumber * item[1]
            dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData  

    def __rtruediv__(self, givenNumber):
        dataAsDict = OrderedDict()
        for item in self.get_data().items():
            time = item[0]
            value = givenNumber * 1.0 / item[1]
            dataAsDict.update({time : value})
        timeSeriesData = TimeSeriesData(givenTimeSeriesDataAsDict = dataAsDict, givenHeaderName = ''.join(['about ', self.__headerName]))
        return timeSeriesData 

    def ts_add(self, givenTimeSeries): # add another time series
        assert(isinstance(givenTimeSeries, TimeSeriesData))
        dataDict = OrderedDict()
        timeList = sorted(self.get_data().keys() & givenTimeSeries.get_data().keys())
        for time in timeList:
            value = self.get_data().get(time) + givenTimeSeries.get_data().get(time)
            dataDict.update({time : value})
        resultTimeSeries = TimeSeriesData(givenTimeSeriesDataAsDict = dataDict, givenHeaderName = ''.join([self.get_header_name(), ' + ', givenTimeSeries.get_header_name()]))
        return resultTimeSeries

    def ts_sub(self, givenTimeSeries): # subtract another time series
        assert(isinstance(givenTimeSeries, TimeSeriesData))
        dataDict = OrderedDict()
        timeList = sorted(self.get_data().keys() & givenTimeSeries.get_data().keys())
        for time in timeList:
            value = self.get_data().get(time) - givenTimeSeries.get_data().get(time)
            dataDict.update({time : value})
        resultTimeSeries = TimeSeriesData(givenTimeSeriesDataAsDict = dataDict, givenHeaderName = ''.join([self.get_header_name(), ' - ', givenTimeSeries.get_header_name()]))
        return resultTimeSeries

    def ts_mul(self, givenTimeSeries): # multipy another time series
        assert(isinstance(givenTimeSeries, TimeSeriesData))
        dataDict = OrderedDict()
        timeList = sorted(self.get_data().keys() & givenTimeSeries.get_data().keys())
        for time in timeList:
            value = self.get_data().get(time) * givenTimeSeries.get_data().get(time)
            dataDict.update({time : value})
        resultTimeSeries = TimeSeriesData(givenTimeSeriesDataAsDict = dataDict, givenHeaderName = ''.join([self.get_header_name(), ' * ', givenTimeSeries.get_header_name()]))
        return resultTimeSeries

    def ts_div(self, givenTimeSeries): # divide another time series
        assert(isinstance(givenTimeSeries, TimeSeriesData))
        dataDict = OrderedDict()
        timeList = sorted(self.get_data().keys() & givenTimeSeries.get_data().keys())
        for time in timeList:
            value = self.get_data().get(time) * 1.0 /  givenTimeSeries.get_data().get(time)
            dataDict.update({time : value})
        resultTimeSeries = TimeSeriesData(givenTimeSeriesDataAsDict = dataDict, givenHeaderName = ''.join([self.get_header_name(), ' / ', givenTimeSeries.get_header_name()]))
        return resultTimeSeries

    pass

class LinePloterSetting(object):
    def __init__(self, givenXLabel, givenYLabel, givenGrid):
        self.__xLabel = givenXLabel
        self.__yLabel = givenYLabel
        self.__gridOn = False
        self.__font = fm.FontProperties(fname = '/home/yawei/Documents/FLBenchmark-toolkit/YaHeiConsolas.ttf')

    def getXLabel(self):
        return self.__xLabel

    def getYLabel(self):
        return self.__yLabel

    def getFont(self):
        return self.__font

    def getGridOn(self):
        return self.__gridOn
    pass

class PloterOfTimeSeriesData(object):
    def __init__(self, givenTimeSeries, givenLinePloterSetting, givenSavedFigPath):
        assert(isinstance(givenTimeSeries, TimeSeriesData))
        assert(isinstance(givenLinePloterSetting, LinePloterSetting))
        self.__timeSeries = givenTimeSeries
        self.__settingInfo = givenLinePloterSetting
        self.__savedFigPath = givenSavedFigPath
        pass

    def plot(self):
        # set font to show Chinese 
        fig = plt.figure() 
        ax1 = fig.add_subplot(1, 1, 1)
        ax1.plot(self.__timeSeries.get_data().keys(), self.__timeSeries.get_data().values(), linewidth = 1) 
        ax1.set_ylabel(self.__settingInfo.getYLabel()) 
        ax1.set_xlabel(self.__settingInfo.getXLabel()) 
        ax1.legend([self.__timeSeries.get_header_name()], prop = self.__settingInfo.getFont())
        ax1.grid(True) 
        plt.savefig(self.__savedFigPath) 
        plt.show()
    pass

class PloterOfMultipleTimeSeriesData(object):
    def __init__(self, givenMultipleTimeSeriesList, givenLinePloterSetting, givenSavedFigPath):
        assert(isinstance(givenLinePloterSetting, LinePloterSetting))
        self.__timeSeriesList = givenMultipleTimeSeriesList
        self.__settingInfo = givenLinePloterSetting
        self.__savedFigPath = givenSavedFigPath
        pass

    def __getTimeTags(self):
        for timeSeriesIndex, timeSeries in enumerate(self.__timeSeriesList):
           if timeSeriesIndex == 0:
               timeTags = timeSeries.getData().keys()
               return timeTags
    
    def __getValues(self):
        timeTags = self.__getTimeTags()
        valueNList = []
        for timeSeriesIndex, timeSeries in enumerate(self.__timeSeriesList):
            valueList = []
            for time in timeTags:
                value = timeSeries.getData().get(time)
                valueList.append(value)
            valueNList.append(valueList)
        return valueNList

    def __getLegends(self):
        legendList = []
        for timeSeriesIndex, timeSeries in enumerate(self.__timeSeriesList):
            legend = timeSeries.getHeaderName()
            legendList.append(legend)
        return legendList

    def plot(self):
        timeTagList = self.__getTimeTags()
        valueNList = self.__getValues()
        legendList = self.__getLegends()
        fig = plt.figure() 
        ax1 = fig.add_subplot(1, 1, 1)
        for valueList in valueNList:
            ax1.plot([int(time) for time in timeTagList], [float(value) for value in valueList], linewidth = 1) 
        ax1.set_ylabel(self.__settingInfo.getYLabel()) 
        ax1.set_xlabel(self.__settingInfo.getXLabel()) 
        ax1.legend(legendList, prop = self.__settingInfo.getFont())
        ax1.grid(self.__settingInfo.getGridOn()) 
        plt.savefig(self.__savedFigPath) 
        plt.show()
    pass

class CsvFile(object):
    def __init__(self, givenFilePath, hasHeader = False):
        self.__filePath = givenFilePath
        self.__recordList = self.read(hasHeader=hasHeader)
    
    def read(self, hasHeader = False):
        resultList = []
        with open(self.__filePath) as f:
            reader = csv.reader(f) 
            if hasHeader == True:
                headerList = [column.strip() for column in str(next(reader)).split(' ')]
            for row in reader: # read file line by line.
                resultList.append(row)
        return resultList

    def getRecords(self):
        return self.__recordList
    pass

class Test(object):
    def testPloterOfMultipleTimeSeriesData(self):
        recordList = CsvFile(givenFilePath='/home/yawei/Documents/LUNA16/candidateOfnodules(500+500)labelUnbalanced/result.csv', hasHeader=True).getRecords()
        testAccuracy = TimeSeriesData(givenTimeSeriesDataAsDict=OrderedDict(zip([record[0] for record in recordList], [record[1] for record in recordList])), givenHeaderName='Test Accuracy')
        testLoss = TimeSeriesData(givenTimeSeriesDataAsDict=OrderedDict(zip([record[0] for record in recordList], [record[2] for record in recordList])), givenHeaderName='Test Loss')
        pmts = PloterOfMultipleTimeSeriesData(givenMultipleTimeSeriesList = [testAccuracy, testLoss], givenLinePloterSetting = LinePloterSetting(givenXLabel='round', givenYLabel='value', givenGrid=False), 
                                              givenSavedFigPath = '/home/yawei/Documents/FLBenchmark-toolkit/resultPloter/candidateOfnodules(500+500)labelUnbalanced.jpg')
        pmts.plot()
    pass

Test().testPloterOfMultipleTimeSeriesData()



























