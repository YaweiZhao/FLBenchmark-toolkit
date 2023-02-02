import os, shutil
import csv
import numpy as np
import time
import json
import nibabel as nib
import SimpleITK as sitk
import matplotlib.pyplot as plt
from skimage.segmentation import clear_border
from skimage.measure import label,regionprops
from skimage.morphology import disk, binary_erosion, binary_closing
from skimage.filters import roberts
from scipy import ndimage as ndi
from skimage import measure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class NpyFile(object):
    def __init__(self, givenFilePath):
        self.__filePath = givenFilePath

    def write(self, givenNumpyArray):
        np.save(file=self.__filePath, arr = givenNumpyArray)

    def read(self):
        npy = np.load(file = self.__filePath)
        return npy
    pass

class TxtFile(object):
    def __init__(self, givenTargetFilePath):
        self.__targetFilePath = givenTargetFilePath
    
    def write(self, givenDataObject):
        if isinstance(givenDataObject, dict):
            with open(self.__targetFilePath, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(givenDataObject, ensure_ascii=False)) # 将dic dumps json 格式进行写入
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

class Luna16(object):
    """
    |--CSVFILES
    |	|--annotations.csv
    |	|--annotations_excluded.csv
    |	|--candidates.csv
    | 	|--sampleSubmission.csv
    |	|--seriesuids.csv
    |--seg-lungs-LUNA16
    |--subset0~9 包含10个子集，每个大约有90个CT扫描，总共888个
    |	|--xxx.mhd：
    |	|--xxx.raw：
    """
    def __init__(self, givenDir = '/home/yawei/MedicalDatasets'):
        self.__dir = givenDir
        self.__uIds = self.__initSeriesUid(givenFilePathOfUid=self.__dir+'/CSVFILES/seriesuids.csv')
        self.__candidateNodules = self.__initCandidateNodules(givenFilePathOfCandidateNodules=self.__dir+'/CSVFILES/candidates.csv')
        self.__annotations = self.__initAnnotation(givenFilePathOfAnnotation=self.__dir+'/CSVFILES/annotations.csv')

    def __initSeriesUid(self, givenFilePathOfUid):
        seriesUidList = CsvFile(givenFilePath=givenFilePathOfUid, hasHeader=False).getRecords() # load every patient's ID.
        return seriesUidList

    def __initCandidateNodules(self, givenFilePathOfCandidateNodules):
        # all candidates like nodules, including macilous/benign or not. totally 551065 candidates.
        # when 'class' is 0, it is not a nodule. 
        # when 'class' is 1, it is a macilous/benign nodule. totally 1351 nodules.
        """
        seriesuid,coordX,coordY,coordZ,class
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-56.08,-67.85,-311.92,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,53.21,-244.41,-245.17,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,103.66,-121.8,-286.62,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-33.66,-72.75,-308.41,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-32.25,-85.36,-362.51,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-26.65,-203.07,-165.07,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-74.99,-114.79,-311.92,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-16.14,-248.61,-239.55,0
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,135.89,-141.41,-252.2,0
        """
        candidateNoduleList = CsvFile(givenFilePath=givenFilePathOfCandidateNodules, hasHeader=True).getRecords()
        return candidateNoduleList
    
    def __initAnnotation(self, givenFilePathOfAnnotation):
        # some nodules. totally 1187. The coordinates here may not be exactly same to those in the file 'candidates.csv'.    
        """
        seriesuid,coordX,coordY,coordZ,diameter_mm
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,-128.6994211,-175.3192718,-298.3875064,5.651470635
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860,103.7836509,-211.9251487,-227.12125,4.224708481
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100398138793540579077826395208,69.63901724,-140.9445859,876.3744957,5.786347814
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100621383016233746780170740405,-24.0138242,192.1024053,-391.0812764,8.143261683
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100621383016233746780170740405,2.441546798,172.4648812,-405.4937318,18.54514997
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100621383016233746780170740405,90.93171321,149.0272657,-426.5447146,18.20857028
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100621383016233746780170740405,89.54076865,196.4051593,-515.0733216,16.38127631
        1.3.6.1.4.1.14519.5.2.1.6279.6001.100953483028192176989979435275,81.50964574,54.9572186,-150.3464233,10.36232088
        1.3.6.1.4.1.14519.5.2.1.6279.6001.102681962408431413578140925249,105.0557924,19.82526014,-91.24725078,21.08961863
        """
        annotationList = CsvFile(givenFilePath=givenFilePathOfAnnotation, hasHeader=True).getRecords()
        return annotationList

    def getSeriesIds(self):
        return self.__uIds

    def getCandidateNodules(self):
        return self.__candidateNodules

    def getAnnotations(self):
        return self.__annotations
    
    def extractCtScan(self, givenSeriesId):
        ctScan = CtScan(givenFilePath=self.__dir+'/rawData/'+givenSeriesId+'.mhd')
        return ctScan

    def extractSliceOfCtScan(self, givenCtScan, givenSliceId):
        assert(isinstance(givenCtScan, CtScan))
        sliceOfCtScan = Slice(givenCtScan=givenCtScan, givenSliceId=givenSliceId)
        return sliceOfCtScan

    def extractCandidateOfNodule(self, givenCtScan, givenWorldCoord, givenClassLabel = '0'): # '0' means not a real nodule, and '1' means a real nodule
        assert(isinstance(givenCtScan, CtScan))
        assert(isinstance(givenWorldCoord, WorldCoord))
        candidateOfNodule = NoduleCandidate(givenCtScan=givenCtScan, givenWorldCoordOfNodule=givenWorldCoord, givenClassLabel=givenClassLabel)
        return candidateOfNodule
    
    def extractCollectionOfCandidateOfNodule(self, givenMaxNumber = 100):
        """
        givenMaxNumber can choose an integer like 100, or 'infty'.
        """
        if givenMaxNumber == 'infty':
            givenMaxNumber = len(self.getCandidateNodules())
        noduleList, otherList = [], []
        candidateOfNodules = self.getCandidateNodules()
        for candidateIndex, candidate in enumerate(candidateOfNodules[0:givenMaxNumber]):
            nodule = self.__generateCandidateOfNodule(givenCandidateSettingRecord = candidate)
            if candidate[4] == '1':
                noduleList.append(nodule)
                continue
            if candidate[4] == '0':
                otherList.append(nodule)
        return noduleList, otherList
    
    def __generateCandidateOfNodule(self, givenCandidateSettingRecord):
        assert(isinstance(givenCandidateSettingRecord, list))
        ctScan = self.extractCtScan(givenSeriesId=givenCandidateSettingRecord[0])
        worldCoord = WorldCoord(givenX=float(givenCandidateSettingRecord[1]), givenY=float(givenCandidateSettingRecord[2]), givenZ=float(givenCandidateSettingRecord[3])) 
        nodule = self.extractCandidateOfNodule(givenCtScan=ctScan, givenWorldCoord=worldCoord, givenClassLabel = givenCandidateSettingRecord[4])
        return nodule

    def extractUnbalancedCollectionOfCandidateOfNodule(self, givenUnbalancedSetting):
        assert(isinstance(givenUnbalancedSetting, UnbalanceSetting))
        noduleList, otherList = [], []
        candidateOfNodules = self.getCandidateNodules()
        for candidateIndex, candidate in enumerate(candidateOfNodules):
            if np.mod(candidateIndex, 10000) == 0:
                print(candidateIndex)
            if candidate[4] == '1' and len(noduleList) < givenUnbalancedSetting.getNumOfClass1Samples():
                nodule = self.__generateCandidateOfNodule(givenCandidateSettingRecord = candidate)
                noduleList.append(nodule)
                continue
            if candidate[4] == '0' and len(otherList) < givenUnbalancedSetting.getNumOfClass0Samples():
                nodule = self.__generateCandidateOfNodule(givenCandidateSettingRecord = candidate)
                otherList.append(nodule)
        return noduleList, otherList

    def allocateCandidateOfNoduleBasedOnDataFederation(self, givenDataFederation, givenMaxNumber = 'infty'):
        assert(isinstance(givenDataFederation, DataFederation))
        if givenMaxNumber == 'infty':
            self.prepareDataFederationByNpy(givenDataFederation=givenDataFederation, givenMaxNumber=len(self.__candidateNodules))
            return 
        if givenMaxNumber <= 200:
            self.prepareDataFederationByFiles(givenDataFederation=givenDataFederation, givenMaxNumber=givenMaxNumber)
            return 
        if givenMaxNumber > 200:
            self.prepareDataFederationByNpy(givenDataFederation=givenDataFederation, givenMaxNumber=givenMaxNumber)
    
    def prepareDataFederationByFiles(self, givenDataFederation, givenMaxNumber):
        assert(isinstance(givenDataFederation, DataFederation))
        noduleList, otherList = self.extractCollectionOfCandidateOfNodule(givenMaxNumber = givenMaxNumber)
        numberOfClients, configs = givenDataFederation.getNumberOfClients(), givenDataFederation.getConfigSettings()
        idBeginIndexOfClass0, idBeginIndexOfClass1 = 0, 0
        for iclient in range(numberOfClients):
            print('ready to save data of client: ' + str(iclient))
            numberOfSampleOfClass0, numberOfSampleOfClass1 = int(float(configs[iclient][1])*len(otherList)), int(float(configs[iclient][2])*len(noduleList))
            idsOfSamplesOfClass0 = range(idBeginIndexOfClass0, min(idBeginIndexOfClass0+numberOfSampleOfClass0, len(otherList))) # class 0
            idsOfSamplesOfClass1 = range(idBeginIndexOfClass1, min(idBeginIndexOfClass1+numberOfSampleOfClass1, len(noduleList))) # class 1
            class0List, class1List = [otherList[i] for i in idsOfSamplesOfClass0], [noduleList[i] for i in idsOfSamplesOfClass1]
            for samplei in class0List+class1List:
                samplei.save(givenTargetDir = givenDataFederation.getDataFederationDir() + '/client' + str(iclient), givenType = 'jpg')
            idBeginIndexOfClass0, idBeginIndexOfClass1 = min(idBeginIndexOfClass0+numberOfSampleOfClass0, len(otherList)-1), min(idBeginIndexOfClass1+numberOfSampleOfClass1, len(noduleList)-1)

    def prepareDataFederationByNpy(self, givenDataFederation, givenMaxNumber):
        assert(isinstance(givenDataFederation, DataFederation))
        noduleList, otherList = self.extractCollectionOfCandidateOfNodule(givenMaxNumber = givenMaxNumber)
        numberOfClients, configs = givenDataFederation.getNumberOfClients(), givenDataFederation.getConfigSettings()
        idBeginIndexOfClass0, idBeginIndexOfClass1 = 0, 0
        for iclient in range(numberOfClients):
            print('ready to save data of client: ' + str(iclient))
            numberOfSampleOfClass0, numberOfSampleOfClass1 = int(float(configs[iclient][1])*len(otherList)), int(float(configs[iclient][2])*len(noduleList))
            idsOfSamplesOfClass0 = range(idBeginIndexOfClass0, min(idBeginIndexOfClass0+numberOfSampleOfClass0, len(otherList))) # class 0
            idsOfSamplesOfClass1 = range(idBeginIndexOfClass1, min(idBeginIndexOfClass1+numberOfSampleOfClass1, len(noduleList))) # class 1
            class0Array, class1Array = np.array([otherList[i] for i in idsOfSamplesOfClass0]), np.array([noduleList[i] for i in idsOfSamplesOfClass1])
            NpyFile(givenFilePath=givenDataFederation.getDataFederationDir() + '/client' + str(iclient) + '/' + 'class0.npy').write(givenNumpyArray=class0Array)
            NpyFile(givenFilePath=givenDataFederation.getDataFederationDir() + '/client' + str(iclient) + '/' + 'class1.npy').write(givenNumpyArray=class1Array)
            idBeginIndexOfClass0, idBeginIndexOfClass1 = min(idBeginIndexOfClass0+numberOfSampleOfClass0, len(otherList)-1), min(idBeginIndexOfClass1+numberOfSampleOfClass1, len(noduleList)-1)

    def prepareUnbalancedDataFederation(self, givenDataFederation, givenUnbalanceSetting):
        assert(isinstance(givenDataFederation, DataFederation))
        assert(isinstance(givenUnbalanceSetting, UnbalanceSetting))
        noduleList, otherList = self.extractUnbalancedCollectionOfCandidateOfNodule(givenUnbalancedSetting=givenUnbalanceSetting)
        nodulesForFederation, othersForFederation = noduleList[0:givenUnbalanceSetting.getNumOfClass1Samples()], otherList[0:givenUnbalanceSetting.getNumOfClass0Samples()]
        numberOfClients, configs = givenDataFederation.getNumberOfClients(), givenDataFederation.getConfigSettings()
        idBeginIndexOfClass0, idBeginIndexOfClass1 = 0, 0
        for iclient in range(numberOfClients):
            print('ready to save data of client: ' + str(iclient))
            numberOfSampleOfClass0, numberOfSampleOfClass1 = int(float(configs[iclient][1])*len(othersForFederation)), int(float(configs[iclient][2])*len(nodulesForFederation))
            idsOfSamplesOfClass0 = range(idBeginIndexOfClass0, min(idBeginIndexOfClass0+numberOfSampleOfClass0, len(othersForFederation))) # class 0
            idsOfSamplesOfClass1 = range(idBeginIndexOfClass1, min(idBeginIndexOfClass1+numberOfSampleOfClass1, len(nodulesForFederation))) # class 1
            candidatesOfClienti =  [othersForFederation[i] for i in idsOfSamplesOfClass0] + [nodulesForFederation[i] for i in idsOfSamplesOfClass1]
            for indexOfSample, samplei in enumerate(candidatesOfClienti):
                samplei.save(givenTargetDir = givenDataFederation.getDataFederationDir() + '/client' + str(iclient), givenType = 'jpg')
            idBeginIndexOfClass0, idBeginIndexOfClass1 = min(idBeginIndexOfClass0+numberOfSampleOfClass0, len(othersForFederation)-1), min(idBeginIndexOfClass1+numberOfSampleOfClass1, len(nodulesForFederation)-1)
    
    def allocateCandidateOfNoduleBasedOnUnbalanceDataFederation(self, givenDataFederation, givenUnbalanceSetting):
        self.prepareUnbalancedDataFederation(givenDataFederation=givenDataFederation, givenUnbalanceSetting=givenUnbalanceSetting)
    pass

class UnbalanceSetting(object):
    def __init__(self, givenClass0Size = 100, givenClass1Size = 100):
        self.__numberOfClass0Samples = givenClass0Size
        self.__numberOfClass1Samples = givenClass1Size
    
    def getNumOfClass1Samples(self):
        return self.__numberOfClass1Samples

    def getNumOfClass0Samples(self):
        return self.__numberOfClass0Samples
    pass

class DataFederation(object):
    """
    prepare data federation, like:
    Client id	Class 0	Class 1
    0	        0.1	    0.6
    1	        0.3	    0.3
    2	        0.6	    0.1
    """
    def __init__(self, givenConfigPath, givenDataFederationDir):
        self.__configRecords = CsvFile(givenFilePath=givenConfigPath, hasHeader=True).getRecords()
        self.__numOfClients = len(self.__configRecords)
        self.__numOfClass = len(self.__configRecords[0])-1
        self.__dataFederationDir = givenDataFederationDir
        self.__configPath = givenConfigPath
        self.__checkDataFederationSetting()
        pass

    def getConfigSettings(self):
        return self.__configRecords

    def getNumberOfClients(self):
        return self.__numOfClients

    def getDataFederationDir(self):
        return self.__dataFederationDir

    def getConfigPath(self):
        return self.__configPath

    def getNumberOfClass(self):
        return self.__numOfClass
    
    def clear(self):
        dirs = os.listdir(self.__dataFederationDir)
        for dir in dirs:
            path = os.path.join(self.__dataFederationDir,dir)
            if os.path.isdir(path) == True:
                shutil.rmtree(path)
        pass

    def __checkDataFederationSetting(self):
        self.clear()
        for clientId in range(self.__numOfClients):
            dataDirOfClient = self.__dataFederationDir + '/client' + str(clientId)
            if os.path.exists(dataDirOfClient) == False:
                os.makedirs(dataDirOfClient)
            for classId in range(self.__numOfClass):
                dataDirOfClass = dataDirOfClient + '/' + str(classId)
                if os.path.exists(dataDirOfClass) == False:
                    os.makedirs(dataDirOfClass)
        pass
    pass

class WorldCoord(object):
    def __init__(self, givenX, givenY, givenZ):
        self.__X, self.__Y, self.__Z = givenX, givenY, givenZ
        
    def get(self):
        return self.__X, self.__Y, self.__Z
    pass

class VoxelCoord(object):
    def __init__(self, givenWorldCoord, givenOriginCoord, givenSpacing):
        assert(isinstance(givenWorldCoord, WorldCoord))
        self.__worldCoord = givenWorldCoord
        self.__X, self.__Y, self.__Z = self.init(givenOriginCoord, givenSpacing)
    
    def init(self, givenOriginCoord, givenSpacing):
        """
        init x, y, z, and keep the `int` part
        """
        assert(isinstance(givenOriginCoord, WorldCoord))
        stretchedVoxelCoord = np.absolute(np.array(self.__worldCoord.get()) - np.array(givenOriginCoord.get()))
        eles = stretchedVoxelCoord / givenSpacing
        eles = [int(ele) for ele in eles] # do not use float, instead by int 
        return eles

    def get(self):
        return self.__X, self.__Y, self.__Z
    pass

class SettingAboutCtScan(object):
    def __init__(self, givenFilePath):
        self.__itkimage = sitk.ReadImage(givenFilePath)

    def getOriginCoord(self):
        xVal, yVal, zVal = np.array(list(self.__itkimage.GetOrigin()))
        return WorldCoord(xVal, yVal, zVal)   # CT原点坐标

    def getSpacing(self):
        return np.array(list(self.__itkimage.GetSpacing()))  # CT像素间隔
    pass

class SettingAboutSlice(object):
    def __init__(self, givenSliceId):
        self.__threshold = -400 # for mask
        self.__sliceId = givenSliceId
    
    def getThreshold(self):
        return self.__threshold
    pass

class SettingAboutNodule(object):
    def __init__(self, givenWorldCoordOfNodule):
        self.__worldCoord = givenWorldCoordOfNodule
        self.__radiusOfBox = 30
        self.__pad = 2

    def getWorldCoord(self):
        return self.__worldCoord

    def getRadiusOfBox(self): # radiusOfBox是正方形边长一半
        return self.__radiusOfBox

    def getPad(self): # pad是边的宽度
        return self.__pad
    pass

class IdGenerator(object):
    def __init__(self):
        self.__idNumber = time.time()
    
    def get(self):
        return str(self.__idNumber)
    pass

class NoduleCandidate(object):
    def __init__(self, givenCtScan, givenWorldCoordOfNodule, givenClassLabel):
        assert(isinstance(givenCtScan, CtScan))
        self.__ctScanPath = givenCtScan.getPath()
        self.__worldCoord = givenWorldCoordOfNodule
        self.__classLabel = self.__initLabel(givenClassLabel)
        self.__settingObj = SettingAboutNodule(givenWorldCoordOfNodule=self.__worldCoord)
        self.__voxelCoord = VoxelCoord(givenWorldCoord=self.__settingObj.getWorldCoord(), givenOriginCoord=givenCtScan.getSetting().getOriginCoord(), givenSpacing=givenCtScan.getSetting().getSpacing())
    
    def __initLabel(self, givenClassLabel):
        if givenClassLabel == '1':
            return '1' #'class1-'
        if givenClassLabel == '0':
            return '0' #'class0-'

    def getVoxelCoord(self):
        return self.__voxelCoord
    
    def __extractSlice(self):
        ctScan = CtScan(givenFilePath=self.__ctScanPath)
        sliceImg = ctScan.extractSliceByCoord(givenWorldCoord=self.__worldCoord)
        return sliceImg

    def getImg(self):
        sliceImg = self.__extractSlice()
        x,y,z = self.__voxelCoord.get() # 注意 y代表纵轴，x代表横轴
        noduleImg = sliceImg[max(0, y - self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[0], y + self.__settingObj.getRadiusOfBox()),
                                    max(0, x - self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[1], x + self.__settingObj.getRadiusOfBox())]
        return noduleImg

    def highlight2DByBox(self): 
        sliceImg = self.__extractSlice()
        x,y,z = self.__voxelCoord.get() # 注意 y代表纵轴，x代表横轴
        sliceImg[max(0, y - self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[0], y + self.__settingObj.getRadiusOfBox()),
                        max(0, x - self.__settingObj.getRadiusOfBox() - self.__settingObj.getPad()):max(0, x - self.__settingObj.getRadiusOfBox())] = 3000 # 竖线

        sliceImg[max(0, y - self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[0], y + self.__settingObj.getRadiusOfBox()),
                        min(sliceImg.shape[1], x + self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[1], x + self.__settingObj.getRadiusOfBox() + self.__settingObj.getPad())] = 3000 # 竖线

        sliceImg[max(0, y - self.__settingObj.getRadiusOfBox() - self.__settingObj.getPad()):max(0, y - self.__settingObj.getRadiusOfBox()),
                        max(0, x - self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[1], x + self.__settingObj.getRadiusOfBox())] = 3000 # 横线

        sliceImg[min(sliceImg.shape[0], y + self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[0], y + self.__settingObj.getRadiusOfBox() + self.__settingObj.getPad()),
                        max(0, x - self.__settingObj.getRadiusOfBox()):min(sliceImg.shape[1], x + self.__settingObj.getRadiusOfBox())] = 3000 # 横线
        plt.figure(1)
        plt.imshow(sliceImg, cmap='gray')
        plt.show()

    def save(self, givenTargetDir, givenType = 'nii'):
        targetPath = givenTargetDir + '/' + self.__classLabel + '/' + IdGenerator().get() + '.' + givenType
        img = self.getImg()
        if givenType == 'nii':
            new_img = nib.nifti1.Nifti1Image(img, None, header=None)
            nib.save(new_img, targetPath)
        if givenType == 'jpeg' or givenType == 'jpg':
            plt.figure(1)
            plt.imshow(img, cmap='gray')
            plt.axis('off')
            plt.savefig(targetPath)
        pass
    pass

class Slice(object):
    def __init__(self, givenCtScan, givenSliceId):
        assert(isinstance(givenCtScan, CtScan))
        self.__image = givenCtScan.extractSliceById(givenSliceId=givenSliceId)
        self.__settingObj = SettingAboutSlice(givenSliceId=givenSliceId)

    def __directBinary(self):
        binaryImg = self.__image < self.__settingObj.getThreshold() # Step 1: Convert into a binary image. 
        return binaryImg
    
    def __removeBlob(self, givenBinaryImg):
        cleared = clear_border(givenBinaryImg) # Step 2: Remove the blobs connected to the border of the image.
        return cleared

    def __labelConnectedRegions(self, givenClearBinaryImg):
        labelImg = label(givenClearBinaryImg) # Step 3: Label the image.
        return labelImg

    def __extractLabeledRegions(self, givenLabelImg, givenNumberOfRegions = 2):
        """
        Step 4: Keep the labels with 2 largest areas.
        """
        areas = [r.area for r in regionprops(givenLabelImg)] 
        areas.sort()
        if len(areas) > givenNumberOfRegions:
            for region in regionprops(givenLabelImg):
                if region.area < areas[-givenNumberOfRegions]:
                    for coordinates in region.coords:                
                        givenLabelImg[coordinates[0], coordinates[1]] = 0
        binaryImg = givenLabelImg > 0
        return binaryImg
    
    def __erosionForSeparateNoduleFromBloodVessels(self, givenBinaryImg):
        selem = disk(2)
        binary = binary_erosion(givenBinaryImg, selem)
        return binary

    def __closureForNoduleAttachedLungWall(self, givenBinaryImg):
        selem = disk(10)
        binary = binary_closing(givenBinaryImg, selem)
        edges = roberts(binary)
        binary = ndi.binary_fill_holes(edges)
        return binary

    def segmentLungs(self):
        '''
        This funtion segments the lungs from the given 2D slice.
        '''
        binary = self.__directBinary(threshold=self.__settingObj.getThreshold()) # Step 1: Convert into a binary image. 
        cleared = self.__removeBlob(givenBinaryImg=binary) # Step 2: Remove the blobs connected to the border of the image.
        labelImg = self.__labelConnectedRegions(givenClearBinaryImg=cleared) # Step 3: Label the image.
        binary = self.__extractLabeledRegions(givenLabelImg=labelImg) # Step 4: Keep the labels with 2 largest areas.
        binary = self.__erosionForSeparateNoduleFromBloodVessels(givenBinaryImg=binary) # Step 5: Erosion operation with a disk of radius 2. This operation is to seperate the lung nodules attached to the blood vessels.
        binary = self.__closureForNoduleAttachedLungWall(givenBinaryImg=binary) # Step 6: Closure operation with a disk of radius 10. This operation is to keep nodules attached to the lung wall.
        return binary

    def show(self):
        plt.figure(1)
        plt.imshow(self.__image)
        plt.show()
    
    def showMask(self):
        mask = self.segmentLungs()
        plt.figure(1)
        plt.imshow(mask)
        plt.show()
    pass

class CtScan(object):
    def __init__(self, givenFilePath):
        self.__filePath = givenFilePath
        self.__itkimage = sitk.ReadImage(givenFilePath)
        self.__numpyImage = sitk.GetArrayFromImage(self.__itkimage)
        self.__settingObj = SettingAboutCtScan(givenFilePath=givenFilePath)
        pass
    
    def extractSliceByCoord(self, givenWorldCoord):
        x, y, z = VoxelCoord(givenWorldCoord=givenWorldCoord, givenOriginCoord=self.__settingObj.getOriginCoord(), givenSpacing=self.__settingObj.getSpacing()).get()
        slice = self.__numpyImage[z]
        return slice

    def extractSliceById(self, givenSliceId):
        dataOfSlice = np.squeeze(self.__numpyImage[givenSliceId])
        return dataOfSlice
    
    def show3dUndone(self, threshold=-400):
        # Position the scan upright, 
        # so the head of the patient would be at the top facing the camera
        p = self.__numpyImage.transpose(2,1,0)
        verts,faces, normals, vals = measure.marching_cubes(p, threshold)
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        # Fancy indexing: `verts[faces]` to generate a collection of triangles
        mesh = Poly3DCollection(verts[faces], alpha=0.1)
        face_color = [0.5, 0.5, 1]
        mesh.set_facecolor(face_color)
        ax.add_collection3d(mesh)
        ax.set_xlim(0, p.shape[0])
        ax.set_ylim(0, p.shape[1])
        ax.set_zlim(0, p.shape[2])
        plt.show()
    
    def getSetting(self):
        return self.__settingObj

    def getData(self):
        return self.__numpyImage

    def getPath(self):
        return self.__filePath
    pass



class Test(object):
    def __init__(self):
        pass
    
    def testLuna16AllocateCandidateOfNoduleBasedOnDataFederation(self):
        luna16 = Luna16(givenDir='/home/yawei/Documents/LUNA16')
        df = DataFederation(givenConfigPath='/home/yawei/Documents/LUNA16/candidateOfnodules/dataFederationConfig.csv', givenDataFederationDir='/home/yawei/Documents/LUNA16/candidateOfnodules')
        luna16.allocateCandidateOfNoduleBasedOnDataFederation(givenDataFederation=df, givenMaxNumber=100)
    
    def testLuna16AllocateCandidateOfNoduleBasedOnUnbalanceDataFederation(self):
        luna16 = Luna16(givenDir='/home/yawei/Documents/LUNA16')
        df = DataFederation(givenConfigPath='/home/yawei/Documents/LUNA16/candidateOfnodules/dataFederationConfig.csv', givenDataFederationDir='/home/yawei/Documents/LUNA16/candidateOfnodules')
        luna16.allocateCandidateOfNoduleBasedOnUnbalanceDataFederation(givenDataFederation=df, givenUnbalanceSetting=UnbalanceSetting(givenClass0Size=500, givenClass1Size=500))
        

    def testLuna16NoduleHighlighBox(self):
        ctScan = CtScan(givenFilePath='/home/yawei/Documents/LUNA16/rawData/1.3.6.1.4.1.14519.5.2.1.6279.6001.119304665257760307862874140576.mhd')
        wc = WorldCoord(givenX=-114.849876257,	givenY = 153.690289006, givenZ=-689.672451967)
        nodule = NoduleCandidate(givenCtScan=ctScan, givenWorldCoordOfNodule=wc, givenClassLabel='1')
        nodule.highlight2DByBox()
    pass

Test().testLuna16AllocateCandidateOfNoduleBasedOnUnbalanceDataFederation()



















