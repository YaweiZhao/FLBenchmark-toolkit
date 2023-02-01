"""
- Pre-run

pip install SimpleITK
"""

import SimpleITK as sitk
import matplotlib.pyplot as plt 

class MhdUnit(object):
    def __init__(self, givenMhdFilePath):
        self.__mhdFilePath = givenMhdFilePath # path ends with ".mhd"
        self.__fileName = self.__extractFileName()
        pass
    
    def __extractFileName(self):
        elementList = self.__mhdFilePath.split('/')
        fileName = elementList[-1]
        return fileName

    def load(self):
        sitkImg = sitk.ReadImage(self.__mhdFilePath)
        return sitkImg

    def getImgArray(self):
        sitkImg = self.load()
        imgArray = sitk.GetArrayFromImage(sitkImg) # z, y, x
        return imgArray
    
    def extract1Slice(self, givenSliceId = (1, None, None)):
        imgArray = self.getImgArray()
        zid, yid, xid = givenSliceId
        if zid != None:
            return imgArray[zid,:,:]
        if yid != None:
            return imgArray[:,yid,:]
        if xid != None:
            return imgArray[:,:,xid]

    def __saveAsNiigz(self, givenTargetDir):
        sitkImg = self.load()
        targetPath = givenTargetDir + self.__fileName[:self.__fileName.find(".mhd")] + ".nii"
        sitk.WriteImage(sitkImg, fileName=targetPath)
    
    def save(self, givenTargetDir, givenTargetType = 'nii'):
        if givenTargetType == 'nii':
            self.__saveAsNiigz(givenTargetDir)

    def showSlice(self, givenSliceId = (1, None, None)):
        plt.figure(1)
        dataOfSlice = self.extract1Slice(givenSliceId=givenSliceId)
        plt.imshow(dataOfSlice)
        plt.show()
    pass




class Test(object):
    def execute(self):
        mhdo = MhdUnit(givenMhdFilePath="/home/yawei/Documents/LUNA16/rawData/1.3.6.1.4.1.14519.5.2.1.6279.6001.102681962408431413578140925249.mhd")
        # convert to a nii.gz 
        #mhdo.save(givenTargetDir="/home/yawei/my-flbenchmark/toyData/mhd2nii/", givenTargetType="nii")
        # show 1 slice
        mhdo.showSlice(givenSliceId=(15,None, None))
        
Test().execute()














