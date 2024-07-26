import multiprocessing as mp
import os
import sys
import threading
from tkinter import Toplevel
from typing import TYPE_CHECKING, List, Tuple, Union

import napari
from napari.layers import Image
from napari_spfluo import ManualAbInitioWidget
from napari_spfluo._utils_widgets import FilterSetWidget
from pwfluo import objects as pwfluoobj
from pwfluo.objects import FluoImage, Particle, PSFModel, SetOfCoordinates3D
from pwfluo.protocols import ProtFluoBase
from pyworkflow.gui.dialog import ToolbarListDialog
from pyworkflow.gui.tree import TreeProvider
from pyworkflow.utils.process import runJob
from pyworkflow.viewer import DESKTOP_TKINTER, View, Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QWidget
from scipy.ndimage import affine_transform
from spfluo.utils.transform import get_transform_matrix_around_center

from singleparticle import Plugin
from singleparticle.constants import VISUALISATION_MODULE
from singleparticle.convert import save_boundingboxes

if TYPE_CHECKING:
    from qtpy.QtWidgets import QListWidgetItem


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
            self._views.append(SetOfParticlesView(obj))
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


class NapariSetOfParticlesWidget(Toplevel):
    def __init__(self, particles: pwfluoobj.SetOfParticles, master=None):
        super().__init__(master)
        self.withdraw()
        if self.winfo_viewable():
            self.transient(master)

        self.queue = mp.Queue(maxsize=particles.getSize())
        print(f"{__name__=}")
        self.process = mp.Process(
            target=self.lanchNapariForParticles,
            daemon=True,
            args=(particles, self.queue),
        )
        self.process.start()
        print("yooooo")

    def lanchNapariForParticles(
        self, particles: pwfluoobj.SetOfParticles, queue: mp.Queue
    ):
        vs_xy, vs_z = particles.getVoxelSize()
        self.particles = [p for p in particles]
        self.particles_data_not_transformed = [
            p.getDataIsotropic()[0] for p in particles.iterItems()
        ]
        self.particles_data_transformed = []
        self.particles_data = self.particles_data_not_transformed
        viewer = napari.Viewer()

        self.widget = FilterSetWidget()
        self.widget.set_data(self.particles_data)
        viewer.window.add_dock_widget(self.widget)
        self.particle_layer: list[Image] = viewer.add_image(
            data=self.particles_data[0], channel_axis=0
        )
        viewer.bind_key("Delete", self._on_delete)
        self.widget.list_widget.currentItemChanged.connect(self._on_item_changed)

        # add transform button
        transform_layout = QHBoxLayout()
        checkbox_widget = QWidget()
        checkbox_widget.setLayout(transform_layout)
        self.check_box = QCheckBox()
        transform_layout.addWidget(QLabel("transform"))
        transform_layout.addWidget(self.check_box)
        self.widget.layout().addWidget(checkbox_widget)

        self.check_box.stateChanged.connect(self._on_transform_changed)

        napari.run()
        queue.put(self.widget.mask_indices_image.tolist())

    # def _on_layer_changed(self, image_layer: napari.layers.Image):
    #    if image_layer and (image_layer.ndim == 4 or image_layer.ndim == 5):
    #        self.current_image_layer = image_layer
    #        self.original_data = np.copy(self.current_image_layer.data)
    #        self.widget.set_data(list(image_layer.data))

    def _on_item_changed(self, item: "QListWidgetItem", previous: "QListWidgetItem"):
        i = self.widget.list_widget.row(item)
        for c in range(self.particles_data[0].shape[0]):
            self.particle_layer[c].data = self.particles_data[i][c]
            self.particle_layer[c].refresh()

    def _on_delete(self, viewer: napari.Viewer):
        indices_deleted = self.widget._on_delete()
        for idx in indices_deleted:
            self.particles.pop(idx)
            self.particles_data_not_transformed.pop(idx)
            if self.particles_data_transformed:
                self.particles_data_transformed.pop(idx)

    def _on_transform_changed(self, state: int):
        assert isinstance(state, int)
        match state:
            case Qt.CheckState.Unchecked:
                self.particles_data = self.particles_data_not_transformed
            case Qt.CheckState.Checked:
                if not self.particles_data_transformed:
                    # populate particles_data_transformed
                    for p in self.particles:
                        p: pwfluoobj.Particle
                        data, _ = p.getDataIsotropic()
                        transform = p.getTransform()
                        if transform:
                            H = get_transform_matrix_around_center(
                                data.shape[1:], transform.getRotationMatrix()
                            )
                            H[:3, 3] += transform.getShifts()
                            for c in range(data.shape[0]):
                                data[c] = affine_transform(data[c], H)
                        self.particles_data_transformed.append(data)
                self.particles_data = self.particles_data_transformed

        self.widget.set_data(self.particles_data)
        current_row = self.widget.list_widget.currentRow()
        for c in range(self.particles_data[0].shape[0]):
            self.particle_layer[c].data = self.particles_data[current_row][c]
            self.particle_layer[c].refresh()


class SetOfParticlesView(View):
    def __init__(self, particles: pwfluoobj.SetOfParticles):
        self.particles = particles

    def show(self):
        return NapariSetOfParticlesWidget(self.particles)


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
        save_boundingboxes(coords_im, csv_path)
        program = Plugin.getSPFluoProgram([VISUALISATION_MODULE, "coords"])
        args = [path, "--coords", csv_path]
        vs_xy, vs_z = im.getVoxelSize()
        args += ["--scale", str(vs_z), str(vs_xy), str(vs_xy)]
        runJob(None, program, args, env=Plugin.getEnviron())


# Stupid view


class NapariManualAbInitioWidget(Toplevel):
    def __init__(
        self,
        side_particle: Particle,
        top_particle: Particle,
        psf: PSFModel,
        channel: int,
        master=None,
    ):
        super().__init__(master)
        self.withdraw()
        if self.winfo_viewable():
            self.transient(master)

        self.queue = mp.Queue(maxsize=1)
        print(f"{__name__}")
        self.process = mp.Process(
            target=self._launch_napari,
            daemon=True,
            args=(side_particle, top_particle, psf, channel, self.queue),
        )
        print("starting process")
        self.process.start()
        print("kill!")
        # self.process.kill()
        print("yooooooooo")
        # stuff I want to execute

    def _launch_napari(
        self,
        side_particle: Particle,
        top_particle: Particle,
        psf: PSFModel,
        channel: int,
        queue: mp.Queue,
    ):
        viewer = napari.Viewer()
        # _, widget = viewer.window.add_plugin_dock_widget("napari-spfluo", "Manual ab initio reconstruction")

        side_data, side_pixel_size = (
            side_particle.getData()[channel],
            side_particle.getVoxelSize(),
        )
        top_data, top_pixel_size = (
            top_particle.getData()[channel],
            top_particle.getVoxelSize(),
        )
        psf_data, psf_pixel_size = psf.getData()[channel], psf.getVoxelSize()

        pixel_size_to_scale = lambda ps_xy, ps_z: (ps_z, ps_xy, ps_xy)

        side_layer = viewer.add_image(
            side_data, name="side", scale=pixel_size_to_scale(*side_pixel_size)
        )
        top_layer = viewer.add_image(
            top_data,
            name="top",
            visible=False,
            scale=pixel_size_to_scale(*top_pixel_size),
        )
        psf_layer = viewer.add_image(
            psf_data,
            name="psf",
            visible=False,
            scale=pixel_size_to_scale(*psf_pixel_size),
        )
        widget = ManualAbInitioWidget(viewer, top_layer, side_layer, psf_layer)
        viewer.window.add_dock_widget(widget)
        print(f"{id(viewer)=}", viewer.layers, file=sys.stderr)
        # widget._reconstruction_layer.events.set_data.connect(lambda: )

        napari.run()

        queue.put(
            {
                "data": widget._reconstruction_layer.data,
                "scale": widget._reconstruction_layer.scale,
            }
        )


class ManualAbInitioView(View):
    def __init__(
        self,
        side_particle: Particle,
        top_particle: Particle,
        psf: PSFModel,
        channel: int,
    ):
        self.side_particle = side_particle
        self.top_particle = top_particle
        self.psf = psf
        self.channel = channel

    def show(self):
        return NapariManualAbInitioWidget(
            self.side_particle, self.top_particle, self.psf, self.channel
        )
