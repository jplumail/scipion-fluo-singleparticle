import math
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Union
import typing
from pyworkflow.object import Integer, String, Pointer, CsvList, Object, Scalar, Set, Boolean # type: ignore
import pyworkflow.utils as pwutils # type: ignore

import os
import numpy as np
from numpy.typing import NDArray
import json

from ome_types import OME
from aicsimageio import AICSImage
from aicsimageio.writers.ome_tiff_writer import OmeTiffWriter
from scipy.ndimage import affine_transform # type: ignore


NO_INDEX = 0

class Matrix(Scalar):
    def __init__(self, **kwargs) -> None:
        Scalar.__init__(self, **kwargs)
        self._matrix: NDArray[np.float64] = np.eye(4)

    def _convertValue(self, value: str) -> None:
        """Value should be a str with comma separated values
        or a list.
        """
        self._matrix = np.array(json.loads(value)).astype(np.float64)

    def getObjValue(self) -> str:
        self._objValue = json.dumps(self._matrix.tolist())
        return self._objValue

    def setValue(self, i: int, j: int, value: float) -> None:
        self._matrix[i, j] = value

    def getMatrix(self) -> NDArray[np.float64]:
        """ Return internal numpy matrix. """
        return self._matrix

    def setMatrix(self, matrix: NDArray[np.float64]) -> None:
        """ Override internal numpy matrix. """
        self._matrix = matrix

    def __str__(self) -> str:
        return np.array_str(self._matrix)

    def _copy(self, other: 'Matrix') -> None:
        """ Override the default behaviour of copy
        to also copy array data.
        Copy other into self.
        """
        self.setMatrix(np.copy(other.getMatrix()))
        self._objValue = other._objValue


class Transform(Object):
    """ This class will contain a transformation matrix
    that can be applied to 2D/3D objects like images and volumes.
    It should contain information about euler angles, translation(or shift)
    and mirroring.
    Shifts are stored in pixels as treated in extract coordinates, or assign angles,...
    """

    # Basic Transformation factory
    ROT_X_90_CLOCKWISE = 'rotX90c'
    ROT_Y_90_CLOCKWISE = 'rotY90c'
    ROT_Z_90_CLOCKWISE = 'rotZ90c'
    ROT_X_90_COUNTERCLOCKWISE = 'rotX90cc'
    ROT_Y_90_COUNTERCLOCKWISE = 'rotY90cc'
    ROT_Z_90_COUNTERCLOCKWISE = 'rotZ90cc'

    def __init__(self, matrix: Optional[NDArray[np.float64]]=None, **kwargs):
        Object.__init__(self, **kwargs)
        self._matrix = Matrix()
        if matrix is not None:
            self.setMatrix(matrix)

    def getMatrix(self) -> NDArray[np.float64]:
        return self._matrix.getMatrix()

    def getRotationMatrix(self) -> NDArray[np.float64]:
        M = self.getMatrix()
        return M[:3, :3]

    def getShifts(self) -> NDArray[np.float64]:
        M = self.getMatrix()
        return M[:3, 3]

    def getMatrixAsList(self) -> List:
        """ Return the values of the Matrix as a list. """
        return self._matrix.getMatrix().flatten().tolist()

    def setMatrix(self, matrix: NDArray[np.float64]):
        self._matrix.setMatrix(matrix)

    def __str__(self) -> str:
        return str(self._matrix)

    def scale(self, factor: float) -> None:
        m = self.getMatrix()
        m *= factor
        m[3, 3] = 1.

    def scaleShifts(self, factor: float) -> None:
        # By default Scipion uses a coordinate system associated with the volume rather than the projection
        m = self.getMatrix()
        m[:3, 3] *= factor

    def invert(self) -> Matrix:
        """Inverts the transformation and returns the matrix"""
        self._matrix.setMatrix(np.linalg.inv(self._matrix.getMatrix()))
        return self._matrix

    def setShifts(self, x: float, y: float, z: float) -> None:
        m = self.getMatrix()
        m[0, 3] = x
        m[1, 3] = y
        m[2, 3] = z

    def setShiftsTuple(self, shifts: Tuple[float, float, float]) -> None:
        self.setShifts(shifts[0], shifts[1], shifts[2])

    def composeTransform(self, matrix: np.ndarray) -> None:
        """Apply a transformation matrix to the current matrix """
        new_matrix = np.matmul(matrix, self.getMatrix())
        # new_matrix = matrix * self.getMatrix()
        self._matrix.setMatrix(new_matrix)

    @classmethod
    def create(cls, type: str) -> 'Transform':
        """Creates a default Transform object.
        Type is a string: `rot[X,Y,Z]90[c,cc]`
        with `c` meaning clockwise and `cc` counter clockwise
        """
        if type == cls.ROT_X_90_CLOCKWISE:
            return Transform(matrix=np.array([
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, -1, 0, 0],
                [0, 0, 0, 1]]))
        elif type == cls.ROT_X_90_COUNTERCLOCKWISE:
            return Transform(matrix=np.array([
                [1, 0, 0, 0],
                [0, 0, -1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1]]))
        elif type == cls.ROT_Y_90_CLOCKWISE:
            return Transform(matrix=np.array([
                [1, 0, -1, 0],
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1]]))
        elif type == cls.ROT_Y_90_COUNTERCLOCKWISE:
            return Transform(matrix=np.array([
                [1, 0, 1, 0],
                [0, 1, 0, 0],
                [-1, 0, 0, 0],
                [0, 0, 0, 1]]))
        elif type == cls.ROT_Z_90_CLOCKWISE:
            return Transform(matrix=np.array([
                [0, 1, 0, 0],
                [-1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]]))
        elif type == cls.ROT_Z_90_COUNTERCLOCKWISE:
            return Transform(matrix=np.array([
                [0, -1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]]))
        else:
            TRANSFORMATION_FACTORY_TYPES = [
                cls.ROT_X_90_CLOCKWISE,
                cls.ROT_Y_90_CLOCKWISE,
                cls.ROT_Z_90_CLOCKWISE,
                cls.ROT_X_90_COUNTERCLOCKWISE,
                cls.ROT_Y_90_COUNTERCLOCKWISE,
                cls.ROT_Z_90_COUNTERCLOCKWISE
            ]
            raise Exception('Introduced Transformation type is not recognized.\nAdmitted values are\n'
                            '%s' % ' '.join(TRANSFORMATION_FACTORY_TYPES))


class ImageDim(CsvList):
    """ Just a wrapper to a CsvList to store image dimensions
    as X, Y and Z.
    """

    def __init__(self, x: Optional[int]=None, y: Optional[int]=None, z: Optional[int]=None) -> None:
        CsvList.__init__(self, pType=int)
        if x is not None and y is not None:
            self.append(x)
            self.append(y)
            if z is not None:
                self.append(z)

    def getX(self) -> Optional[int]:
        if self.isEmpty():
            return None
        return self[0]

    def getY(self) -> Optional[int]:
        if self.isEmpty():
            return None
        return self[1]

    def getZ(self) -> Optional[int]:
        if self.isEmpty():
            return None
        return self[2]

    def set(self, dims: Tuple[int, int, int]):
        if self.isEmpty():
            for i in range(3):
                self.append(dims[i])
        else:
            self[:] = dims

    def __str__(self) -> str:
        x, y, z = self.getX(), self.getY(), self.getZ()
        if (x is None) or (y is None) or (z is None):
            s = 'No-Dim'
        else:
            s = '%d x %d' % (x, y)
            if z > 1:
                s += ' x %d' % z
        return s


class SamplingRate(CsvList):
    """ Just a wrapper to a CsvList to store a sampling rate
    as XY and Z.
    """

    def __init__(self, xy: Optional[float]=None, z: Optional[float]=None):
        CsvList.__init__(self, pType=float)
        if xy is not None and z is not None:
            self.append(xy)
            self.append(z)
    
    def setSR(self, xy: float, z: float) -> None:
        if self.isEmpty():
            self.append(xy)
            self.append(z)
        else:
            self[0], self[1] = xy, z

    def getSR(self) -> Optional[Tuple[float, float]]:
        if self.isEmpty():
            return None
        return self[0], self[1]

    def __str__(self) -> str:
        sr = self.getSR()
        if sr is None:
            s = 'No-Dim'
        else:
            xy, z = sr
            s = '%d x %d' % (xy, xy)
            s += ' x %d' % z
        return s


class Image(Object):
    """Represents an image object"""

    def __init__(self, filename: Optional[str]=None, **kwargs) -> None:
        """
         Params:
        :param location: Could be a valid location: (index, filename)
        or  filename
        """
        Object.__init__(self, **kwargs)
        # Image location is composed by an index and a filename
        self._filename: String = String()
        self._img: Optional[AICSImage] = None
        self._samplingRate: SamplingRate = SamplingRate()
        # _transform property will store the transformation matrix
        # this matrix can be used for 2D/3D alignment or
        # to represent projection directions
        self._transform: Transform = Transform()
        # default origin by default is box center =
        # (Xdim/2, Ydim/2,Zdim/2)*sampling
        # origin stores a matrix that using as input the point (0,0,0)
        # provides  the position of the actual origin in the system of
        # coordinates of the default origin.
        # _origin is an object of the class Transform shifts
        # units are A.
        self._origin: Transform = Transform()
        self._imageDim: ImageDim = ImageDim()
        if filename:
            self.setFileName(filename)
    
    def isEmpty(self):
        return self._img is None

    def getSamplingRate(self) -> Optional[Tuple[float, float]]:
        """ Return image sampling rate. (A/pix) """
        return self._samplingRate.getSR()

    def setSamplingRate(self, sampling: Tuple[float, float]) -> None:
        self._samplingRate.setSR(*sampling)

    def getFormat(self):
        pass

    def getDataType(self):
        pass

    def getDimensions(self) -> Optional[Tuple[int, int, int]]:
        """getDimensions is redundant here but not in setOfImages
         create it makes easier to create protocols for both images
         and sets of images
        """
        return self.getDim()

    def getDim(self) -> Union[Tuple[int, int, int], None]:
        """Return image dimensions as tuple: (Xdim, Ydim, Zdim)"""
        x, y, z = self._imageDim.get()
        if (x is None) or (y is None) or (z is None):
            return None
        return x, y, z
    
    def getXDim(self) -> Union[int, None]:
        if self._imageDim.getX() is None:
            return None
        return self._imageDim.getX()

    def getYDim(self) -> Union[int, None]:
        if self._imageDim.getY() is None:
            return None
        return self._imageDim.getY()

    def getFileName(self) -> str:
        """ Use the _objValue attribute to store filename. """
        fname = self._filename.get()
        if fname is None:
            raise ValueError("Image has no filename!")
        return fname

    def setFileName(self, filename: str) -> None:
        """ Use the _objValue attribute to store filename. """
        self._filename.set(filename)
        self._img = AICSImage(filename)
        x, y, z = self._img.dims.shape
        self._imageDim.set((x, y, z))
    
    def getBaseName(self) -> str:
        return os.path.basename(self.getFileName())

    def copyInfo(self, other: 'Image') -> None:
        """ Copy basic information """
        self.copyAttributes(other, '_samplingRate')

    def copyFilename(self, other: 'Image')-> None:
        """ Copy location index and filename from other image. """
        self.setFileName(other.getFileName())

    def hasTransform(self) -> bool:
        return self._transform is not None

    def getTransform(self)-> Transform:
        return self._transform

    def setTransform(self, newTransform: Transform) -> None:
        self._transform = newTransform

    def hasOrigin(self) -> bool:
        return self._origin is not None

    def getOrigin(self) -> Transform:
        """shifts in A"""
        if self.hasOrigin():
            return self._origin
        else:
            return self._getDefaultOrigin()

    def _getDefaultOrigin(self) -> Transform:
        sampling = self.getSamplingRate()
        dim = self.getDim()
        if sampling is None or dim is None:
            return Transform()
        t = Transform()
        x, y, z = dim
        t.setShifts(float(x) / -2. * sampling[0], float(y) / -2. * sampling[0], float(z) * sampling[1])
        return t  # The identity matrix

    def getShiftsFromOrigin(self) -> Tuple[float, float, float]:
        origin = self.getOrigin().getShifts()
        x = origin[0]
        y = origin[1]
        z = origin[2]
        return x, y, z
        # x, y, z are floats in Angstroms

    def setShiftsInOrigin(self, x: float, y: float, z: float) -> None:
        origin = self.getOrigin()
        origin.setShifts(x, y, z)

    def setOrigin(self, newOrigin: Transform) -> None:
        """If None, default origin will be set.
        Note: shifts are in Angstroms"""
        if newOrigin:
            self._origin = newOrigin
        else:
            self._origin = self._getDefaultOrigin()

    def originResampled(self, originNotResampled: Transform, oldSampling: SamplingRate) -> Optional[Transform]:
        if self.getSamplingRate() is None or oldSampling.getSR() is None:
            raise RuntimeError("Sampling rate is None")
        factor = np.array(self.getSamplingRate()) / np.array(oldSampling.getSR())
        shifts = originNotResampled.getShifts()
        origin = self.getOrigin()
        origin.setShifts(shifts[0] * factor[0],
                         shifts[1] * factor[0],
                         shifts[2] * factor[1])
        return origin

    def __str__(self) -> str:
        """ String representation of an Image. """
        dim = self.getDim()
        dimStr = str(ImageDim(*dim)) if dim else 'No-Dim'
        sr = self.getSamplingRate()
        if sr:
            xy_res, z_res = sr
            return ("%s (%s, %0.2fx%0.2fx%0.2f Å/px)" % (self.getClassName(), dimStr,
                                            xy_res, xy_res, z_res)) # FIX units
        return ("%s (%s, %0.2fx%0.2fx%0.2f Å/px)" % (self.getClassName(), dimStr, 1., 1., 1.))

    def getFiles(self) -> set:
        return set([self.getFileName()])
    
    def build_ome(self, image_name: Optional[str]=None) -> OME:
        im = self._img
        if im is None:
            raise ValueError("Image is None.")
        return OmeTiffWriter.build_ome(
            data_shapes=[im.shape],
            data_types=[im.dtype],
            dimension_order=[im.dims.order],
            channel_names=[im.channel_names],
            image_name=[image_name] if image_name else [None],
            physical_pixel_sizes=[im.physical_pixel_sizes],
            channel_colors=[None],
        )
    
    def save(self, apply_transform=False) -> None:
        if self._img is None:
            raise ValueError("Image is None.")
        if apply_transform:
            im_data = affine_transform(self._img, self.getTransform().getMatrix())
        else:
            im_data = self._img.data
        
        OmeTiffWriter.save(
            data=im_data,
            uri=self.getFileName(),
            ome_xml=self.build_ome()
        )


class PSFModel(Image): # TODO: intérêt de cette classe?
    """ Represents a generic PSF model. """

class FluoImage(Image):
    """Represents a fluo object"""
    IMG_ID_FIELD = '_imgId'

    def __init__(self, **kwargs) -> None:
        """
         Params:
        :param location: Could be a valid location: (index, filename)
        or  filename
        """
        Image.__init__(self, **kwargs)
        # Image location is composed by an index and a filename
        self._psfModel: Optional[PSFModel] = None
        self._imgId: String = String(kwargs.get('imgId', None))
    
    def getImgId(self) -> Union[str, None]:
        """ Get unique image ID, usually retrieved from the
        file pattern provided by the user at the import time.
        """
        return self._imgId.get()

    def setImgId(self, value: str) -> None:
        self._imgId.set(value)

    def hasPSF(self) -> bool:
        return self._psfModel is not None

    def getPSF(self) -> Optional[PSFModel]:
        """ Return the PSF model """
        return self._psfModel

    def setPSF(self, newPSF: PSFModel) -> None:
        self._psfModel = newPSF

class Coordinate3D(Object):
    """This class holds the (x,y,z) position and other information
    associated with a coordinate"""

    IMAGE_ID_ATTR: str = "_imageId"

    def __init__(self, **kwargs) -> None:
        Object.__init__(self, **kwargs)
        self._boxSize: int = 0
        self._imagePointer: Pointer = Pointer(objDoStore=False) # points to a FluoImage
        self._transform: Transform = Transform()
        self._groupId: Integer = Integer(0)  # This may refer to a mesh, ROI, vesicle or any group of coordinates
        self._imageId = String(kwargs.get('imageId', None))  # Used to access to the corresponding image from each coord (it's the tsId)

    def setMatrix(self, matrix: NDArray[np.float64], convention: Optional[str]=None) -> None:
        #self._eulerMatrix.setMatrix(convertMatrix(matrix, direction=const.SET, convention=convention))
        self._transform.setMatrix(matrix)

    def getMatrix(self, convention: Optional[str]=None) -> NDArray[np.float64]:
        return self._transform.getMatrix()

    def eulerAngles(self) -> NDArray[np.float64]:
        R = self.getMatrix()
        sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6
        if not singular:
            x = math.atan2(R[2, 1], R[2, 2])
            y = math.atan2(-R[2, 0], sy)
            z = math.atan2(R[1, 0], R[0, 0])

        else:
            x = math.atan2(-R[1, 2], R[1, 1])
            y = math.atan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])

    def getFluoImage(self) -> Union[FluoImage, None]:
        """ Return the tomogram object to which
        this coordinate is associated.
        """
        return self._imagePointer.get()

    def setFluoImage(self, image: FluoImage) -> None:
        """ Set the micrograph to which this coordinate belongs. """
        self._imagePointer.set(image)

    def getImageId(self) -> str:
        return self._imageId.get()

    def setImageId(self, imageId) -> None:
        self._imageId.set(imageId)

    def getImageName(self) -> Union[str, None]:
        im = self.getFluoImage()
        if im is None:
            return None
        return im.getFileName()

    def getGroupId(self) -> int:
        return self._groupId.get()

    def setGroupId(self, groupId) -> None:
        self._groupId.set(groupId)

    def hasGroupId(self) -> bool:
        return self._groupId is not None

    def __str__(self) -> str:
        return f"Coordinate3D: <{str(self._imagePointer)}, {self._imageId}, {self._groupId}, {self._transform}>"


class Particle(FluoImage):
    """The coordinate associated to each particle is not scaled. To do that, the coordinates and the particles
    sampling rates should be compared (because of how the extraction protocol works). But when shifts are applied to
    the coordinates, it has to be considered that if we're operating with coordinates coming from particles, those
    shifts will be scaled, but if the coordinates come from coordinates, they won't be."""

    IMAGE_NAME_FIELD = "_imageName"
    COORD_VOL_NAME_FIELD = "_coordinate.%s" % Coordinate3D.IMAGE_ID_ATTR
    def __init__(self, **kwargs) -> None:
        FluoImage.__init__(self, **kwargs)
        # This coordinate is NOT SCALED. To do that, the coordinates and subtomograms sampling rates
        # should be compared (because of how the extraction protocol works)
        self._coordinate: Optional[Coordinate3D] = None
        self._imageName: String = String()

    def hasCoordinate3D(self) -> bool:
        return self._coordinate is not None

    def setCoordinate3D(self, coordinate: Coordinate3D) -> None:
        self._coordinate = coordinate

    def getCoordinate3D(self) -> Union[Coordinate3D, None]:
        """Since the object Coordinate3D needs a volume, use the information stored in the
        SubTomogram to reconstruct the corresponding Tomogram associated to its Coordinate3D"""
        return self._coordinate

    def getImageName(self) -> Union[String, None]:
        """ Return the tomogram filename if the coordinate is not None.
        or have set the _imageName property.
        """
        if self._imageName.hasValue():
            return self._imageName.get()
        return None

    def setImageName(self, imageName: str) -> None:
        self._imageName.set(imageName)

class FluoSet(Set):
    _classesDict = None

    def _loadClassesDict(self) -> Dict:

        if self._classesDict is None:
            from pyworkflow.plugin import Domain # type: ignore
            self._classesDict = Domain.getObjects()
            self._classesDict.update(globals())

        return self._classesDict

    def copyInfo(self, other: 'FluoSet') -> None:
        """ Define a dummy copyInfo function to be used
        for some generic operations on sets.
        """
        pass

    def clone(self):
        """ Override the clone defined in Object
        to avoid copying _mapperPath property
        """
        pass

    def copyItems(
        self,
        otherSet: 'FluoSet',
        updateItemCallback: Optional[Callable[[Object, Optional[Any]], Any]]=None,
        itemDataIterator: Optional[Iterator]=None,
        copyDisabledItems: bool=False,
        doClone: bool=True
    ) -> None:
        """ Copy items from another set, allowing to update items information
        based on another source of data, paired with each item.

        Params:
            otherSet: input set from where the items will be copied.
            updateItemCallback: if not None, this will be called for each item
                and each data row (if the itemDataIterator is not None). Apart
                from setting item values or new attributes, it is possible to
                set the special flag _appendItem to False, and then this item
                will not be added to the set.
            itemDataIterator: if not None, it must be an iterator that have one
                data item for each item in the set. Usually the data item is a
                data row, coming from a table stored in text files (e.g STAR)
            copyDisabledItems: By default, disabled items are not copied from the other
                set. If copyDisable=True, then the enabled property of the item
                will be ignored.
            doClone: By default, the new item that will be inserted is a "clone"
                of the input item. By using doClone=False, the same input item
                will be passed to the callback and added to the set. This will
                avoid the clone operation and the related overhead.
        """
        itemDataIter = itemDataIterator  # shortcut

        for item in otherSet:
            # copy items if enabled or copyDisabledItems=True
            if copyDisabledItems or item.isEnabled():
                newItem = item.clone() if doClone else item
                if updateItemCallback:
                    row = None if itemDataIter is None else next(itemDataIter)
                    updateItemCallback(newItem, row)
                # If updateCallBack function returns attribute
                # _appendItem to False do not append the item
                if getattr(newItem, "_appendItem", True):
                    self.append(newItem)
            else:
                if itemDataIter is not None:
                    next(itemDataIter)  # just skip disabled data row

    @classmethod
    def create(
        cls,
        outputPath: str,
        prefix: Optional[str]=None,
        suffix: Optional[str]=None,
        ext: Optional[str]=None,
        **kwargs
    ) -> 'FluoSet':
        """ Create an empty set from the current Set class.
         Params:
            outputPath: where the output file will be written.
            prefix: prefix of the created file, if None, it will be deduced
                from the ClassName.
            suffix: additional suffix that will be added to the prefix with a
                "_" in between.
            ext: extension of the output file, be default will use .sqlite
        """
        fn = prefix or cls.__name__.lower().replace('setof', '')

        if suffix:
            fn += '_%s' % suffix

        if ext and ext[0] == '.':
            ext = ext[1:]
        fn += '.%s' % (ext or 'sqlite')

        setPath = os.path.join(outputPath, fn)
        pwutils.cleanPath(setPath)

        return cls(filename=setPath, **kwargs)

    def createCopy(
        self,
        outputPath: str,
        prefix: Optional[str]=None,
        suffix: Optional[str]=None,
        ext: Optional[str]=None,
        copyInfo: bool=False,
        copyItems: bool=False
    ) -> 'FluoSet':
        """ Make a copy of the current set to another location (e.g file).
        Params:
            outputPath: where the output file will be written.
            prefix: prefix of the created file, if None, it will be deduced
                from the ClassName.
            suffix: additional suffix that will be added to the prefix with a
                "_" in between.
            ext: extension of the output file, be default will use the same
                extension of this set filename.
            copyInfo: if True the copyInfo will be called after set creation.
            copyItems: if True the copyItems function will be called.
        """
        setObj = self.create(
            outputPath, 
            prefix=prefix,
            suffix=suffix,
            ext=ext or pwutils.getExt(self.getFileName())
        )

        if copyInfo:
            setObj.copyInfo(self)

        if copyItems:
            setObj.copyItems(self)

        return setObj

    def getFiles(self) -> set:
        return Set.getFiles(self)


class SetOfImages(Set):
    """ Represents a set of Images """
    ITEM_TYPE: Object = Image

    def __init__(self, **kwargs):
        Set.__init__(self, **kwargs)
        self._samplingRate = SamplingRate()
        self._dim = ImageDim()  # Dimensions of the first image

    def append(self, image: Image) -> None:
        """ Add a image to the set. """
        if image.isEmpty():
            raise ValueError(f"Image {image} is empty!")
        # If the sampling rate was set before, the same value
        # will be set for each image added to the set
        sr = self.getSamplingRate()
        im_sr = image.getSamplingRate()
        if (sr is not None) and (im_sr is None):
            image.setSamplingRate(sr)
        elif (sr is not None) and (im_sr is not None):
            if sr != im_sr:
                raise ValueError(f"{image} has different sampling rate than {self}, found {sr} and {im_sr}")
        elif (sr is None) and (im_sr is not None):
            self.setSamplingRate(im_sr)
        else:
            pass

        dim = self.getDim()
        im_dim = image.getDim()
        if im_dim is None:
            raise ValueError(f"Image {image} dimension is None.")
        if dim is not None:
            if dim != im_dim:
                raise ValueError(f"{image} has different dimension than {self}, found {dim} and {im_dim}")
        else:
            self.setDim(im_dim)

        Set.append(self, image)

    def setDim(self, dim: Tuple[int, int, int]) -> None:
        """ Store dimensions.
        This function should be called only once, to avoid reading
        dimension from image file. """
        self._dim.set(dim)

    def copyInfo(self, other: 'SetOfImages') -> None:
        """ Copy basic information (sampling rate and psf)
        from other set of images to current one"""
        self.copyAttributes(other, '_samplingRate')

    def getFiles(self) -> set:
        filePaths = set()
        uniqueFiles = self.aggregate(['count'], '_filename', ['_filename'])

        for row in uniqueFiles:
            filePaths.add(row['_filename'])
        return filePaths

    def setDownsample(self, downFactor: float) -> None:
        """ Update the values of samplingRate and scannedPixelSize
        after applying a downsampling factor of downFactor.
        """
        sr = self.getSamplingRate()
        if sr is None:
            raise RuntimeError("Couldn't downsample, sampling rate is not set")
        self.setSamplingRate((sr[0]*downFactor, sr[1]*downFactor))

    def setSamplingRate(self, samplingRate: Tuple[float, float]) -> None:
        """ Set the sampling rate and adjust the scannedPixelSize. """
        self._samplingRate.setSR(*samplingRate)

    def getSamplingRate(self) -> Union[Tuple[float, float], None]:
        return self._samplingRate.getSR()
    
    def writeSet(
        self,
        applyTransform: bool=False
    ) -> None:
        for img in self:
            img.save(apply_transform=applyTransform)

    @classmethod
    def create_image(cls, filename):
        return cls.ITEM_TYPE(filename=filename)

    def readSet(self, files: List[str]) -> None:
        """ Populate the set with the images in the stack """
        for i in range(len(files)):
            img = self.create_image(files[i])
            self.append(img)

    def getDim(self) -> Union[Tuple[int, int, int], None]:
        """ Return the dimensions of the first image in the set. """
        if self._dim.isEmpty():
            return None
        dims = self._dim
        x, y, z = dims.getX(), dims.getY(), dims.getZ()
        if (x is None) or (y is None) or (z is None):
            return None
        return x, y, z

    def getDimensions(self) -> Union[Tuple[int, int, int], None]:
        """Return first image dimensions as a tuple: (xdim, ydim, zdim)"""
        return self.getFirstItem().getDim()

    def __str__(self) -> str:
        """ String representation of a set of images. """
        s = "%s (%d items, %s, %s%s)" % \
            (self.getClassName(), self.getSize(),
             self._dimStr(), self._samplingRateStr(), self._appendStreamState())
        return s
    def _samplingRateStr(self) -> str:
        """ Returns how the sampling rate is presented in a 'str' context."""
        sampling = self.getSamplingRate()

        if not sampling:
            raise RuntimeError("Sampling rate is not set")

        return f"{sampling:.2f} Å/px" # FIXME unités

    def _dimStr(self) -> str:
        """ Return the string representing the dimensions. """
        return str(self._dim)

    def appendFromImages(self, imagesSet: 'SetOfImages') -> None:
        """ Iterate over the images and append
        every image that is enabled.
        """
        for img in imagesSet:
            if img.isEnabled():
                self.append(img)

    def appendFromClasses(self, classesSet):
        """ Iterate over the classes and the element inside each
        class and append to the set all that are enabled.
        """
        for cls in classesSet:
            if cls.isEnabled() and cls.getSize() > 0:
                for img in cls:
                    if img.isEnabled():
                        self.append(img)


class SetOfFluoImages(SetOfImages):
    """Represents a set of fluo images"""
    ITEM_TYPE = FluoImage
    REP_TYPE = FluoImage
    EXPOSE_ITEMS = True

    def __init__(self, *args, **kwargs) -> None:
        SetOfImages.__init__(self, **kwargs)
        self._psf: Optional[PSFModel] = None
    
    def hasPSF(self) -> bool:
        return self._psf is not None

    def append(self, image: FluoImage) -> None:
        """ Add a fluo image to the set. """
        if image.isEmpty():
            raise ValueError(f"Image {image} is empty!")

        if image.hasPSF() and self.hasPSF():
            if self._psf != image.getPSF():
                raise ValueError(f"Image {image} PSF does not match with {self}'s PSF, found {image.getPSF()} and {self._psf}!")
        elif image.hasPSF() and not self.hasPSF():
            self._psf = image.getPSF()
        
        SetOfImages.append(self, image)

class SetOfCoordinates3D(FluoSet):
    """ Encapsulate the logic of a set of volumes coordinates.
    Each coordinate has a (x,y,z) position and is related to a Volume
    """
    ITEM_TYPE = Coordinate3D

    def __init__(self, **kwargs) -> None:
        FluoSet.__init__(self, **kwargs)
        self._boxSize: Integer = Integer()
        self._samplingRate: SamplingRate = SamplingRate()
        self._precedentsPointer: Pointer = Pointer() # Points to the SetOfFluoImages associated to
        self._images: Optional[Dict[str, FluoImage]] = None

    def getBoxSize(self) -> int:
        """ Return the box size of the particles.
        """
        return self._boxSize.get()

    def setBoxSize(self, boxSize: int) -> None:
        """ Set the box size of the particles. """
        self._boxSize.set(boxSize)

    def getSamplingRate(self) -> Union[Tuple[float, float], None]:
        """ Return the sampling rate of the particles. """
        return self._samplingRate.getSR()

    def setSamplingRate(self, sampling: Tuple[float, float]) -> None:
        """ Set the sampling rate of the particles. """
        self._samplingRate.setSR(*sampling)

    def iterImages(self) -> Iterable[FluoImage]:
        """ Iterate over the objects set associated with this
        set of coordinates.
        """
        return iter(self.getPrecedents())

    def iterImageCoordinates(self, image: FluoImage):
        """ Iterates over the set of coordinates belonging to that micrograph.
        """
        pass

    def iterCoordinates(self, image: Optional[FluoImage] = None, orderBy: str='id') -> Iterable[Coordinate3D]:
        """ Iterate over the coordinates associated with an image.
        If image=None, the iteration is performed over the whole
        set of coordinates.

        IMPORTANT NOTE: During the storing process in the database, Coordinates3D will lose their
        pointer to ther associated FluoImage. This method overcomes this problem by retrieving and
        relinking the FluoImage as if nothing would ever happened.

        It is recommended to use this method when working with Coordinates3D, being the common
        "iterItems" deprecated for this set.

        Example:

            >>> for coord in coordSet.iterItems()
            >>>     print(coord.getVolName())
            >>>     Error: Tomogram associated to Coordinate3D is NoneType (pointer lost)
            >>> for coord in coordSet.iterCoordinates()
            >>>     print(coord.getVolName())
            >>>     '/path/to/Tomo.file' retrieved correctly

        """

        # Iterate over all coordinates if imgId is None,
        # otherwise use imgId to filter the where selection
        if image is None:
            coordWhere = '1'
        elif isinstance(image, FluoImage):
            coordWhere = '%s="%s"' % ('_imgId', image.getImgId())
        else:
            raise Exception('Invalid input image of type %s'
                            % type(image))


        # Iterate over all coordinates if imgId is None,
        # otherwise use imgId to filter the where selection
        for coord in self.iterItems(where=coordWhere, orderBy=orderBy):
            # Associate the fluo image
            self._associateImage(coord)
            yield coord

    def _getFluoImage(self, imgId: str) -> FluoImage:
        """ Returns the image from an imgId"""
        imgs = self._images
        if imgs is None:
            imgs = dict()
        
        images = self._getFluoImages()
        if imgId not in images.keys():
            im = self.getPrecedents()[{"_imgId": imgId}]
            imgs[imgId] = im
            return im
        else:
            return imgs[imgId]

    def _getFluoImages(self) -> Dict[str, FluoImage]:
        imgs = self._images
        if imgs is None:
            imgs = dict()

        return imgs

    def getPrecedents(self) -> SetOfFluoImages:
        """ Returns the SetOfFluoImages associated with
                this SetOfCoordinates"""
        return self._precedentsPointer.get()

    def getPrecedent(self, imgId):
        return self.getPrecedentsInvolved()[imgId]

    def setPrecedents(self, precedents: Union[SetOfFluoImages, Pointer]) -> None:
        """ Set the images associated with this set of coordinates.
        Params:
            precedents: Either a SetOfFluoImages or a pointer to it.
        """
        if precedents.isPointer():
            self._precedentsPointer.copy(precedents)
        else:
            self._precedentsPointer.set(precedents)

    def getFiles(self) -> set:
        filePaths = set()
        filePaths.add(self.getFileName())
        return filePaths

    def getSummary(self) -> str:
        summary = []
        summary.append("Number of particles: %s" % self.getSize())
        summary.append("Particle size: %s" % self.getBoxSize())
        return "\n".join(summary)

    def copyInfo(self, other: 'SetOfCoordinates3D') -> None:
        """ Copy basic information (id and other properties) but not _mapperPath or _size
        from other set of objects to current one.
        """
        self.setBoxSize(other.getBoxSize())
        if sr := other.getSamplingRate():
            self.setSamplingRate(sr)
        self.setPrecedents(other.getPrecedents())

    def __str__(self) -> str:
        """ String representation of a set of coordinates. """
        if self._boxSize.hasValue():
            boxSize = self._boxSize.get()
            boxStr = ' %d x %d x %d' % (boxSize, boxSize, boxSize)
        else:
            boxStr = 'No-Box'
        s = "%s (%d items, %s, %s Å/px%s)" % (self.getClassName(), self.getSize(), boxStr,
                                              self.getSamplingRate(), self._appendStreamState())

        return s

    def getFirstItem(self) -> Coordinate3D:
        coord = FluoSet.getFirstItem(self)
        self._associateImage(coord)
        return coord

    def _associateImage(self, coord: Coordinate3D) -> None:
        coord.setFluoImage(self._getFluoImage(coord.getImageId()))

    def __getitem__(self, itemId: int) -> Coordinate3D:
        """Add a pointer to a FluoImage before returning the Coordinate3D"""
        coord = FluoSet.__getitem__(self, itemId)
        self._associateImage(coord)
        return coord

    def getPrecedentsInvolved(self) -> dict:
        """ Returns a list with only the images involved in the particles. May differ when
        subsets are done."""

        uniqueTomos = self.aggregate(['count'], '_imgId', ['_imgId'])

        for row in uniqueTomos:
            imgId = row['_imgId']
            # This should register the image in the internal _images
            self._getFluoImage(imgId)

        return self._images # type: ignore

    def append(self, item: Coordinate3D) -> None:
        if self.getBoxSize() is None and item._boxSize:
            self.setBoxSize(item._boxSize)
        super().append(item)

    def getImgIds(self):
        """ Returns all the TS ID (tomoId) present in this set"""
        imgIds = self.aggregate(["MAX"], '_imgId', ['_imgId'])
        imgIds = [d['_imgId'] for d in imgIds]
        return imgIds

class SetOfParticles(SetOfImages):
    ITEM_TYPE = Particle
    REP_TYPE = Particle
    EXPOSE_ITEMS = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._coordsPointer: Pointer = Pointer()
        self._images: Optional[Dict[str, FluoImage]] = None

    def copyInfo(self, other: 'SetOfParticles') -> None:
        """ Copy basic information (sampling rate and ctf)
        from other set of images to current one"""
        super().copyInfo(other)
        if hasattr(other, '_coordsPointer'):  # Like the vesicles in pyseg
            self.copyAttributes(other, '_coordsPointer')

    def hasCoordinates3D(self) -> bool:
        return self._coordsPointer.hasValue()

    def getCoordinates3D(self, asPointer: bool=False) -> Union[Pointer, SetOfCoordinates3D]:
        """ Returns the SetOfCoordinates associated with
        this SetOfParticles"""

        return self._coordsPointer if asPointer else self._coordsPointer.get()

    def setCoordinates3D(self, coordinates: Union[Pointer, SetOfCoordinates3D]) -> None:
        """ Set the SetOfCoordinates associated with
        this set of particles.
         """
        if isinstance(coordinates, Pointer):
            self._coordsPointer = coordinates
        else:
            self._coordsPointer.set(coordinates) # FIXME: strange?

    def iterCoordinates(self, image: Optional[FluoImage]=None, orderBy: str='id') -> Iterator[Union[Coordinate3D, None]]:
        """ Mimics SetOfCoordinates.iterCoordinates so can be passed to viewers or protocols transparently"""
        if self.hasCoordinates3D():
            for particle in self.iterParticles(image, orderBy=orderBy):
                coord = particle.getCoordinate3D()
                if coord is not None:
                    coord.setObjId(particle.getObjId())
                yield coord
        else:
            yield None

    def iterParticles(self, image: Optional[FluoImage] =None, orderBy: str='id')-> Iterator[Particle]:
        """ Iterates over the particles, enriching them with the related image if apply so coordinate getters and setters will work
        If image=None, the iteration is performed over the whole
        set of particles.

        IMPORTANT NOTE: During the storing process in the database, Coordinates3D will lose their
        pointer to the associated Image. This method overcomes this problem by retrieving and
        relinking the Image as if nothing would ever happend.

        It is recommended to use this method when working with subtomograms, anytime you want to properly use
        its coordinate3D attached object.

        Example:

            >>> for subtomo in subtomos.iterItems()
            >>>     print(subtomo.getCoordinate3D().getX(SCIPION))
            >>>     Error: Tomogram associated to Coordinate3D is NoneType (pointer lost)
            >>> for subtomo in subtomos.iterSubtomos()
            >>>     print(subtomo.getCoordinate3D().getX(SCIPION))
            >>>     330 retrieved correctly

        """
        # Iterate over all Subtomograms if tomoId is None,
        # otherwise use tomoId to filter the where selection
        if image is None:
            particleWhere = '1'
        elif isinstance(image, FluoImage):
            particleWhere = '%s="%s"' % (Particle.IMAGE_NAME_FIELD, image.getImgId()) # TODO: add docs Particle _imageName refers to an FluoImage _imgId
        else:
            raise Exception('Invalid input tomogram of type %s'
                            % type(image))

        for particle in self.iterItems(where=particleWhere, orderBy=orderBy):
            if particle.hasCoordinate3D():
                particle.getCoordinate3D().setVolume(self.getFluoImage(particle))
            yield particle

    def getFluoImage(self, particle: Particle) -> Union[FluoImage, None]:
        """ returns and caches the tomogram related with a subtomogram.
        If the subtomograms were imported and not associated to any tomogram returns None."""

        # Tomogram is stored with the coordinate data
        coord = particle.getCoordinate3D()

        # If there is no coordinate associated
        if coord is None:
            return None

        # Else, there are coordinates
        imgId = coord.getImageId()

        self.initFluoImages()
        self._images = typing.cast(Dict[str, FluoImage], self._images)

        # If tsId is not cached, save both identifiers.
        if imgId not in self._images:
            img = self.getCoordinates3D().getPrecedents()[{FluoImage.IMG_ID_FIELD: imgId}] # type: ignore
            self._images[imgId] = img
            return img
        else:
            return self._images[imgId]

    def initFluoImages(self):
        """ Initialize internal _tomos to a dictionary if not done already"""
        if self._images is None:
            self._images = dict()
        #self._images = typing.cast(Dict[str, FluoImage], self._images)

    def getFluoImages(self) -> Dict[str, FluoImage]:
        """ Returns a list  with only the tomograms involved in the subtomograms. May differ when
        subsets are done."""

        imageId_attr = Particle.COORD_VOL_NAME_FIELD
        if self._images is None:
            self.initFluoImages()
            self._images = typing.cast(Dict[str, FluoImage], self._images)
            uniqueImages = self.aggregate(['count'], imageId_attr, [imageId_attr])
            for row in uniqueImages:
                imgId = row[imageId_attr]
                self._images[imgId] = self.getCoordinates3D().getPrecedents()[{FluoImage.IMG_ID_FIELD: imgId}] # type: ignore

        return self._images