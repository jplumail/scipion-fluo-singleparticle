import os
import threading
from typing import List, Union

from pwfluo import objects as pwfluoobj
from pwfluo.objects import FluoImage, SetOfCoordinates3D
from pwfluo.protocols import ProtFluoBase
from pyworkflow.gui.dialog import ToolbarListDialog
from pyworkflow.gui.tree import TreeProvider
from pyworkflow.protocol import Protocol
from pyworkflow.utils.process import runJob
from pyworkflow.viewer import DESKTOP_TKINTER, View, Viewer

from singleparticle import Plugin
from singleparticle.constants import VISUALISATION_MODULE
from singleparticle.convert import save_translations


class NapariDataViewer(Viewer):
    """Wrapper to visualize different type of objects
    with Napari.
    """

    _environments = [DESKTOP_TKINTER]
    _targets = [
        pwfluoobj.SetOfCoordinates3D,
        pwfluoobj.Image,
        pwfluoobj.SetOfImages,
    ]

    def __init__(self, **kwargs):
        Viewer.__init__(self, **kwargs)
        self._views = []

    def _visualize(self, obj: pwfluoobj.FluoObject, **kwargs) -> List[View]:
        cls = type(obj)

        if issubclass(cls, pwfluoobj.SetOfCoordinates3D):
            self._views.append(SetOfCoordinates3DView(self._tkRoot, obj, self.protocol))
        elif issubclass(cls, pwfluoobj.Image):
            self._views.append(ImageView(obj))
        elif issubclass(cls, pwfluoobj.SetOfParticles):
            self._views.append(SetOfParticlesView(obj, self.protocol))
        elif issubclass(cls, pwfluoobj.SetOfImages):
            self._views.append(SetOfImagesView(obj))

        return self._views


#################
## SetOfImages ##
#################


class SetOfImagesView(View):
    def __init__(self, images: pwfluoobj.SetOfImages):
        self.images = images

    def show(self):
        self.proc = threading.Thread(
            target=self.lanchNapariForSetOfImages, args=(self.images,)
        )
        self.proc.start()

    def lanchNapariForSetOfImages(self, images: pwfluoobj.SetOfImages):
        filenames = [p.getFileName() for p in images]
        ImageView.launchNapari(filenames)


####################
## SetOfParticles ##
####################


class SetOfParticlesView(View):
    def __init__(self, particles: pwfluoobj.SetOfParticles, protocol: Protocol):
        self.particles = particles
        self.protocol = protocol

    def show(self):
        self.proc = threading.Thread(
            target=self.lanchNapariForParticles, args=(self.particles,)
        )
        self.proc.start()

    def lanchNapariForParticles(self, particles: pwfluoobj.SetOfParticles):
        filenames = [p.getFileName() for p in particles]
        program = Plugin.getProgram([VISUALISATION_MODULE, "particles"])
        runJob(None, program, filenames, env=Plugin.getEnviron())


###########
## Image ##
###########


class ImageView(View):
    def __init__(self, image: pwfluoobj.Image):
        self.image = image

    def show(self):
        self.proc = threading.Thread(
            target=self.lanchNapariForImage, args=(self.image,)
        )
        self.proc.start()

    def lanchNapariForImage(self, im: pwfluoobj.Image):
        path = im.getFileName()
        self.launchNapari(os.path.abspath(path))

    @staticmethod
    def launchNapari(path: Union[str, List[str]]):
        runJob(None, Plugin.getNapariProgram(), path, env=Plugin.getEnviron())


########################
## SetOfCoordinates3D ##
########################


class SetOfCoordinates3DView(View):
    def __init__(self, parent, coords: SetOfCoordinates3D, protocol: ProtFluoBase):
        self.coords = coords
        self._tkParent = parent
        self._provider = CoordinatesTreeProvider(self.coords)
        self.protocol = protocol

    def show(self):
        SetOfCoordinates3DDialog(
            self._tkParent, self._provider, self.coords, self.protocol
        )


class CoordinatesTreeProvider(TreeProvider):
    """Populate Tree from SetOfCoordinates3D."""

    def __init__(self, coords: SetOfCoordinates3D):
        TreeProvider.__init__(self)
        self.coords: SetOfCoordinates3D = coords

    def getColumns(self):
        return [("FluoImage", 300), ("# coords", 100)]

    def getObjectInfo(self, im: FluoImage) -> dict:
        path = im.getFileName()
        im_name, _ = os.path.splitext(os.path.basename(path))
        return {"key": im_name, "parent": None, "text": im_name, "values": im.count}

    def getObjectPreview(self, obj):
        return (None, None)

    def getObjectActions(self, obj):
        return []

    def _getObjectList(self) -> List[FluoImage]:
        """Retrieve the object list"""
        fluoimages = list(self.coords.getPrecedents())
        for im in fluoimages:
            im.count = len(list(self.coords.iterCoordinates(im)))
        return fluoimages

    def getObjects(self):
        objList = self._getObjectList()
        return objList


class SetOfCoordinates3DDialog(ToolbarListDialog):
    """
    taken from scipion-em-emantomo/emantomo/viewers/views_tkinter_tree.py:EmanDialog
    This class extend from ListDialog to allow calling
    a Napari subprocess from a list of FluoImages.
    """

    def __init__(
        self,
        parent,
        provider: CoordinatesTreeProvider,
        coords: SetOfCoordinates3D,
        protocol: ProtFluoBase,
        **kwargs
    ):
        self.provider = provider
        self.coords = coords
        self._protocol = protocol
        ToolbarListDialog.__init__(
            self,
            parent,
            "Fluoimage List",
            self.provider,
            allowsEmptySelection=False,
            itemDoubleClick=self.doubleClickOnFluoimage,
            allowSelect=False,
            **kwargs
        )

    def doubleClickOnFluoimage(self, e=None):
        fluoimage: FluoImage = e
        # Yes, creating a set of coordinates is not easy
        coords_im: SetOfCoordinates3D = self._protocol._createSetOfCoordinates3D(
            self.coords.getPrecedents(),
            self._protocol._getOutputSuffix(SetOfCoordinates3D),
        )
        coords_im.setBoxSize(self.coords.getBoxSize())
        for coord in self.coords.iterCoordinates(fluoimage):
            coords_im.append(coord)
        self.proc = threading.Thread(
            target=self.lanchNapariForFluoImage, args=(fluoimage, coords_im)
        )
        self.proc.start()

    def lanchNapariForFluoImage(self, im: FluoImage, coords_im: SetOfCoordinates3D):
        path = im.getFileName()
        csv_path = self._protocol._getExtraPath("coords.csv")
        save_translations(coords_im, csv_path)
        program = Plugin.getProgram([VISUALISATION_MODULE, "coords"])
        runJob(None, program, [path, "--coords", csv_path], env=Plugin.getEnviron())