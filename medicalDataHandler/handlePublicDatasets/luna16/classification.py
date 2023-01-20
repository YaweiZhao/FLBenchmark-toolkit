import csv
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
from skimage.segmentation import clear_border
from skimage.measure import label,regionprops, perimeter
from skimage.morphology import ball, disk, dilation, binary_erosion, remove_small_objects, erosion, closing, reconstruction, binary_closing
from skimage.filters import roberts, sobel
from scipy import ndimage as ndi
import scipy.ndimage
from skimage import measure, feature
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class Luna16(object):
    def __init__(self):
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
        self.__radiusOfBox = 20
        self.__pad = 2
        self.__threshold = -400 # for mask
        self.__sliceId = givenSliceId
    
    def getThreshold(self):
        return self.__threshold
    
    def getRadiusOfBox(self): # radiusOfBox是正方形边长一半
        return self.__radiusOfBox

    def getPad(self): # pad是边的宽度
        return self.__pad
    pass

class SettingAboutNodule(object):
    def __init__(self, givenWorldCoordOfNodule):
        self.__worldCoord = givenWorldCoordOfNodule

    def getWorldCoord(self):
        return self.__worldCoord
    pass

class Nodule(object):
    def __init__(self, givenCtScan, givenWorldCoordOfNodule):
        assert(isinstance(givenCtScan, CtScan))
        self.__settingObj = SettingAboutNodule(givenWorldCoordOfNodule=givenWorldCoordOfNodule)
        self.__voxelCoord = VoxelCoord(givenWorldCoord=self.__settingObj.getWorldCoord(), givenOriginCoord=givenCtScan.getSetting().getOriginCoord(), givenSpacing=givenCtScan.getSetting().getSpacing())
    
    def getVoxelCoord(self):
        return self.__voxelCoord

    def getWorldCoord(self):
        return self.__settingObj.getWorldCoord()
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

    def plotBoxOfNodule(self, givenNodule):
        assert(isinstance(givenNodule, Nodule))
        # 注意 y代表纵轴，x代表横轴
        x,y,z = givenNodule.getVoxelCoord().get()
        self.__image[max(0, y - self.__settingObj.getRadiusOfBox()):min(self.__image.shape[0], y + self.__settingObj.getRadiusOfBox()),
        max(0, x - self.__settingObj.getRadiusOfBox() - self.__settingObj.getPad()):max(0, x - self.__settingObj.getRadiusOfBox())] = 3000 # 竖线

        self.__image[max(0, y - self.__settingObj.getRadiusOfBox()):min(self.__image.shape[0], y + self.__settingObj.getRadiusOfBox()),
        min(self.__image.shape[1], x + self.__settingObj.getRadiusOfBox()):min(self.__image.shape[1], x + self.__settingObj.getRadiusOfBox() + self.__settingObj.getPad())] = 3000 # 竖线

        self.__image[max(0, y - self.__settingObj.getRadiusOfBox() - self.__settingObj.getPad()):max(0, y - self.__settingObj.getRadiusOfBox()),
        max(0, x - self.__settingObj.getRadiusOfBox()):min(self.__image.shape[1], x + self.__settingObj.getRadiusOfBox())] = 3000 # 横线

        self.__image[min(self.__image.shape[0], y + self.__settingObj.getRadiusOfBox()):min(self.__image.shape[0], y + self.__settingObj.getRadiusOfBox() + self.__settingObj.getPad()),
        max(0, x - self.__settingObj.getRadiusOfBox()):min(self.__image.shape[1], x + self.__settingObj.getRadiusOfBox())] = 3000 # 横线
        plt.figure(1)
        plt.imshow(self.__image, cmap='gray')
        plt.show()

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
    
    def show3d(self, threshold=-400):
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
    pass

class NoduleCollections(object):
    def __init__(self, givenPath, givenPatchSizeOfNodule = (48, 48, 48)):
        self.__pathOfConfig = givenPath # path of luna16 dataset
        self.__patchSizeOfNodule = givenPatchSizeOfNodule
        pass
    
    def __loadConfigOfAllNodules(self):
        with open(self.__pathOfConfig) as f:
            reader = csv.reader(f) # read config file line by line, and load the location of every nodule. 
            headers = next(reader)
            for row in reader:
                pass
        return 

    def __extractAllNodules(self):
        params = self.__loadConfigOfAllNodules()
        #noduleList = xxx
        #return noduleList

    def writeAllNodules(self, givenTargetType="jpeg"):
        """
        generate all nodules, more than 0.5 millon nodules.
        """
        nodeList = self.__extractAllNodules()
        
        pass

    def writeSubsetOfNodules(self, givenTargetType="jpeg", givenNumberOfNodules = 200):
        """
        generate toy datasets.
        """
        nodeList = self.__extractAllNodules()
        resultNodeList = nodeList[:givenNumberOfNodules,:,:]
        return resultNodeList

    
    pass


class Test(object):
    def __init__(self):
        pass
    
    def execute(self):
        cts = CtScan(givenFilePath="/home/yawei/my-flbenchmark/toyData/mhd/1.3.6.1.4.1.14519.5.2.1.6279.6001.102681962408431413578140925249.mhd")
        worldCorrdOfNodule = WorldCoord(givenX=105.0558,givenY=19.82526, givenZ=-91.2478)
        nodule = Nodule(givenCtScan=cts,givenWorldCoordOfNodule=worldCorrdOfNodule) 
        x, y, z = VoxelCoord(givenWorldCoord=worldCorrdOfNodule,givenOriginCoord=cts.getSetting().getOriginCoord(),givenSpacing=cts.getSetting().getSpacing()).get()
        Slice(givenCtScan=cts, givenSliceId=z).plotBoxOfNodule(givenNodule=nodule)
        pass
    pass

Test().execute()



















