from enum import Enum

from pwfluo.objects import AverageParticle, Particle, PSFModel
from pwfluo.protocols import ProtFluoBase
from pyworkflow import BETA
from pyworkflow.protocol import Form, Protocol, params

from singleparticle.viewers.napari_viewers import ManualAbInitioView


class outputs(Enum):
    reconstructedVolume = AverageParticle


class ProtSingleParticleManualAbInitio(Protocol, ProtFluoBase):
    """
    Manual ab initio reconstruction
    """

    _label = "manual ab initio reconstruction"
    _devStatus = BETA
    _possibleOutputs = outputs

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form: Form):
        form.addSection(label="Data params")
        form.addParam(
            "sideParticle",
            params.PointerParam,
            pointerClass="Particle",
            label="side particle",
            important=True,
            help="Select a particle seen from the side.",
        )
        form.addParam(
            "topParticle",
            params.PointerParam,
            pointerClass="Particle",
            label="top particle",
            important=True,
            help="Select a particle seen from the top.",
        )
        form.addParam(
            "inputPSF",
            params.PointerParam,
            pointerClass="PSFModel",
            label="PSF",
            important=True,
            help="Select the PSF.",
        )
        form.addParam(
            "channel",
            params.IntParam,
            label="channel?",
            important=True,
            default=0,
        )

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep(self.reconstructStep)

    def reconstructStep(self):
        sideParticle: Particle = self.sideParticle.get()
        topParticle: Particle = self.topParticle.get()
        psf: PSFModel = self.inputPSF.get()
        view = ManualAbInitioView(sideParticle, topParticle, psf, self.channel.get())
        widget = view.show()
        print("wait process to stop...")
        widget.process.join()
        print("process finished. getting the queue...")
        item = widget.queue.get()
        scale_z, _, scale_x = item["scale"]
        pixel_size = (scale_x, scale_z)
        reconstruction = AverageParticle.from_data(
            item["data"][None],
            self._getExtraPath("manual_reconstruction.ome.tiff"),
            voxel_size=pixel_size,
        )
        name = self.OUTPUT_PREFIX + self._getOutputSuffix(AverageParticle)
        self._defineOutputs(**{name: reconstruction})
