import os
import pandas as pd
import random
import json
import numpy as np

random.seed(0)

class LibSvmDataset(object):
    """
    - DESCRIPTION

    Dataset is represented like the LIBSVM dataset.

    - REMARK

    Binary classification, label starts from 0, and increses by 1.
    """
    def __init__(self, givenFnPath, givenNameOfDataset):
        self.__path = givenFnPath
        self.__name = givenNameOfDataset
        self.__dataDict = self.__initDataDict()
        self.__numberOfSamples = len(self.__dataDict.keys())
        self.__numberOfFeatures = len(self.__dataDict.get(1)) - 1 # -1 due to: the first item is the label
        self.__columnName = self.__initColumnName()
        self.__typeOfTask = 0 # 0 means binary classification

    def __initColumnName(self):
        featureNameList = ["x"+str(fid) for fid in range(self.__numberOfFeatures)]
        columnName = ["id", "y"]
        columnName.extend(featureNameList)
        return columnName

    def __initDataDict(self):
        dataDict = dict()
        with open(file = self.__path, encoding='utf-8') as file:
            content = file.read()
       
        for lineId, line in enumerate(content.split('\n')):
            if line.strip() == "": 
                continue
            sample = []
            pairList = line.strip().split(' ')
            for pairId, pairItem in enumerate(pairList):
                if pairId == 0:
                    label = pairItem.strip()
                    sample.append(float(label))
                if pairId > 0:
                    columnId, val = pairItem.split(':') 
                    sample.append(float(val))
            dataDict.update({lineId : sample})
        return dataDict
    
    def getNumberOfSamples(self):
        return self.__numberOfSamples

    def get1Sample(self, givenId):
        sample = self.__dataDict[givenId]
        return sample
    
    def getSamples(self, givenIdList):
        sampleList= []
        for id in givenIdList:
            sample = self.get1Sample(id)
            sample.insert(0, id) # add the id of sample 
            sampleList.append(sample)
        return sampleList

    def getColumnName(self):
        return self.__columnName

    def getNameOfDataset(self):
        return self.__name

    def getTypeOfTask(self):
        return self.__typeOfTask
    pass

class Config(object):
    def __init__(self, givenTrainPercentage):
        self.__trainPercentage = givenTrainPercentage
        pass
    
    def getTrainPercentage(self):
        return self.__trainPercentage

    def getTestPercentage(self):
        return 1 - self.getTrainPercentage()
    pass

class LibSvmConverter(object):
    def __init__(self, givenPathOfRawDataset,givenNameOfDataset):
        """
        - DESCRIPTION

        Given a libsvm dataset, split and convert it to '_main.json', 'train_main.json', and 'test_main.json' file.
        """
        self.__dataset = LibSvmDataset(givenFnPath=givenPathOfRawDataset, givenNameOfDataset=givenNameOfDataset)
        self.__trainIdList = self.__getTrainIdList()
        self.__testIdList = self.__getTestIdList()
        pass
    
    def __getTrainIdList(self):
        percentage = Config(givenTrainPercentage=0.8).getTrainPercentage()
        numberOfTrainSamples = int(self.__dataset.getNumberOfSamples() * percentage) 
        trainIdList = random.sample(range(0, self.__dataset.getNumberOfSamples()), numberOfTrainSamples)
        return trainIdList

    def __getTestIdList(self):
        testIdList = []
        for id in range(0, self.__dataset.getNumberOfSamples()):
            if id not in self.__trainIdList:
                testIdList.append(id)
        return testIdList
    
    def writeSamples2Json(self, givenIdListOfSamples, givenJsonPath):
        samples = self.__dataset.getSamples(givenIdList=givenIdListOfSamples)
        with open(givenJsonPath, "w") as f:
            writenDict = dict()
            writenDict.update({"name" : self.__dataset.getNameOfDataset(),
            "column_name" : self.__dataset.getColumnName(),
            "records" : samples})
            json.dump(writenDict, f, indent=4)
            print("json write done")
        pass
    
    def writeMainfile2TrainJson(self, givenJsonPath):
        contentOfMainFile = {
            "name": self.__dataset.getNameOfDataset(),
            "type": self.__dataset.getTypeOfTask(),
            "label_name": "y",
            "parties": [
                self.__dataset.getNameOfDataset()+"_host",
                self.__dataset.getNameOfDataset()+"_guest"
            ],
            "options": None
        }
        with open(givenJsonPath, "w") as f:
            json.dump(contentOfMainFile, f, indent=4)

    def writeMainfile2TestJson(self, givenJsonPath):
        contentOfMainFile = {
            "name": self.__dataset.getNameOfDataset(),
            "type": self.__dataset.getTypeOfTask(),
            "label_name": "y",
            "parties": [
                self.__dataset.getNameOfDataset()+"_test",
            ],
            "options": None
        }
        with open(givenJsonPath, "w") as f:
            json.dump(contentOfMainFile, f, indent=4)

    def prepareTrain(self):
        self.writeSamples2Json(givenIdListOfSamples=self.__trainIdList, givenJsonPath="/home/yawei/flbenchmark.working/data/breast-cancer/train/"+self.__dataset.getNameOfDataset()+"_host.json")
        self.writeSamples2Json(givenIdListOfSamples=self.__trainIdList, givenJsonPath="/home/yawei/flbenchmark.working/data/breast-cancer/train/"+self.__dataset.getNameOfDataset()+"_guest.json")
        self.writeMainfile2TrainJson(givenJsonPath = "/home/yawei/flbenchmark.working/data/breast-cancer/train/"+"_main.json")
        pass

    def prepareTest(self):
        self.writeSamples2Json(givenIdListOfSamples=self.__testIdList, givenJsonPath="/home/yawei/flbenchmark.working/data/breast-cancer/test/"+self.__dataset.getNameOfDataset()+"_test.json")
        self.writeMainfile2TestJson(givenJsonPath = "/home/yawei/flbenchmark.working/data/breast-cancer/test/"+"_main.json")
        pass

    def execute(self):
        self.prepareTrain()
        self.prepareTest()
    pass


def test():
    LibSvmConverter(givenPathOfRawDataset = "/home/yawei/Documents/libsvm/breast-cancer.txt", givenNameOfDataset="breast-cancer").execute()
test()







