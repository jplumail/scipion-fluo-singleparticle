from pwfluo.objects import FluoImage, Particle, SetOfCoordinates3D, SetOfParticles
from pwfluo.protocols import ProtFluoBase
from pyworkflow import BETA
from pyworkflow.protocol import Form, Protocol, params
from spfluo.utils.separate import separate_centrioles_coords


class ProtSingleParticleSeparate(Protocol, ProtFluoBase):
    """
    Separate 2 centrioles
    """

    OUTPUT_NAME = "separated particles"
    _label = "separate centrioles"
    _devStatus = BETA
    _possibleOutputs = SetOfParticles

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form: Form):
        form.addSection(label="Data params")
        form.addParam(
            "inputCoordinates",
            params.PointerParam,
            pointerClass="SetOfCoordinates3D",
            label="Particles",
            important=True,
            help="coordinates locating pairs of centrioles",
        )
        form.addParam(
            "channel",
            params.IntParam,
            default=0,
            label="Separate on channel?",
            help="Choose the most relevant channel to separate the centrioles.\n"
            "The other channels will be separated too.",
        )
        form.addParam(
            "size",
            params.FloatParam,
            label="Box size (μm)",
            help="Size of the squared box surrounding the centriole",
        )
        form.addParam(
            "threshold",
            params.FloatParam,
            default=0.5,
            expertLevel=params.LEVEL_ADVANCED,
            label="Threshold percentage",
            help="Thresholding as a percentage of the max of the image",
        )
        form.addParam(
            "tukey",
            params.FloatParam,
            default=0.1,
            expertLevel=params.LEVEL_ADVANCED,
            label="Tukey alpha",
            help="Smoothing factor when applying the Tukey window",
        )

    def _insertAllSteps(self):
        self._insertFunctionStep(self.separateStep)

    def separateStep(self):
        input_coordinates: SetOfCoordinates3D = self.inputCoordinates.get()
        output_particles = self._createSetOfParticles(
            self._getOutputSuffix(SetOfParticles)
        )
        output_particles.enableAppend()
        for image in input_coordinates.getPrecedents():
            image: FluoImage
            output_particles.setVoxelSize(image.getVoxelSize())
            vs_xy, vs_z = image.getVoxelSize()
            image_data = image.getData()
            for i, coord in enumerate(input_coordinates.iterCoordinates(image)):
                im1, im2 = separate_centrioles_coords(
                    image=image_data,
                    pos=coord.getPosition(),
                    dim=coord.getDim(),
                    scale=(vs_z, vs_xy, vs_xy),
                    threshold_percentage=self.threshold.get(),
                    output_size=self.size.get(),
                    channel=self.channel.get(),
                    tukey_alpha=self.tukey.get(),
                )
                print(image_data.shape, im1.shape)
                for j, im in enumerate([im1, im2]):
                    p = Particle.from_data(
                        im,
                        self._getExtraPath(f"exctracted-im-{i}-{j}.ome.tiff"),
                        voxel_size=image.getVoxelSize(),
                    )
                    output_particles.append(p)
        output_particles.write()

        name = "ParticlesSeparated" + self._getOutputSuffix(SetOfParticles)
        self._defineOutputs(**{name: output_particles})
