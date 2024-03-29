import os
import threading
from typing import List, Tuple, Union

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
        self._views: List[View] = []

    def _visualize(self, obj: pwfluoobj.FluoObject, **kwargs):
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
        vs = images.getVoxelSize()
        if vs:
            vs_xy, vs_z = vs
            vs = (vs_z, vs_xy, vs_xy)  # ZYX order
        ImageView.launchNapari(filenames, scale=vs)


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
        args = [p.getFileName() for p in particles]
        program = Plugin.getSPFluoProgram([VISUALISATION_MODULE, "particles"])
        vs_xy, vs_z = particles.getVoxelSize()
        args += ["--spacing", str(vs_z), str(vs_xy), str(vs_xy)]
        runJob(None, program, args, env=Plugin.getEnviron())


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
        vs = im.getVoxelSize()
        if vs:
            vs_xy, vs_z = vs
            vs = (vs_z, vs_xy, vs_xy)
        self.launchNapari(os.path.abspath(path), scale=vs)

    @staticmethod
    def launchNapari(
        path: Union[str, List[str]], scale: None | Tuple[float, float, float]
    ):
        args = []
        if scale:
            args += ["--scale", f"{scale[0]},{scale[1]},{scale[2]}"]
        if isinstance(path, str):
            path = [path]
        args = path + args
        runJob(None, Plugin.getNapariProgram(), args, env=Plugin.getEnviron())


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
        **kwargs,
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
            **kwargs,
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
        program = Plugin.getSPFluoProgram([VISUALISATION_MODULE, "coords"])
        runJob(None, program, [path, "--coords", csv_path], env=Plugin.getEnviron())
