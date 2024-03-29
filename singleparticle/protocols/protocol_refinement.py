import os
from enum import Enum

import pyworkflow.protocol.params as params
from pwfluo.objects import (
    AverageParticle,
    Particle,
    PSFModel,
    SetOfParticles,
)
from pwfluo.protocols import ProtFluoBase
from pyworkflow import BETA
from pyworkflow.protocol import Protocol

from singleparticle import Plugin
from singleparticle.constants import REFINEMENT_MODULE, UTILS_MODULE
from singleparticle.convert import read_poses, save_image, save_particles_and_poses


class outputs(Enum):
    reconstructedVolume = AverageParticle
    particles = SetOfParticles


class ProtSingleParticleRefinement(Protocol, ProtFluoBase):
    """
    Refinement
    """

    _label = "refinement"
    _devStatus = BETA
    _possibleOutputs = outputs

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form: params.Form):
        form.addSection("Data params")
        form.addParam(
            "inputParticles",
            params.PointerParam,
            pointerClass="SetOfParticles",
            label="Particles",
            important=True,
            help="Select the input particles.",
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
            "initialVolume",
            params.PointerParam,
            pointerClass="Particle",
            label="Initial volume",
            expertLevel=params.LEVEL_ADVANCED,
            allowsNull=True,
        )
        form.addParam(
            "channel",
            params.IntParam,
            default=0,
            label="Reconstruct on channel?",
            help="This protocol reconstruct an average particle in one channel only.",
        )
        form.addParam(
            "gpu",
            params.BooleanParam,
            default=True,
            label="Use GPU?",
            help="This protocol can use the GPU but it's unstable.",
        )
        form.addParam(
            "minibatch",
            params.IntParam,
            default=0,
            label="Size of a minibatch",
            expertLevel=params.LEVEL_ADVANCED,
            help="The smaller the size, the less memory will be used.\n"
            "0 for automatic minibatch.",
            condition="gpu",
        )
        form.addParam(
            "pad",
            params.BooleanParam,
            default=True,
            expertLevel=params.LEVEL_ADVANCED,
            label="Pad particles?",
        )
        form.addSection(label="Reconstruction params")
        form.addParam(
            "sym",
            params.IntParam,
            default=1,
            label="Symmetry degree",
            help="Adds a cylindrical symmetry constraint.",
        )
        form.addParam(
            "lbda",
            params.FloatParam,
            default=100.0,
            label="Lambda",
            help="Higher results in smoother results.",
        )
        form.addParam(
            "ranges",
            params.StringParam,
            label="Ranges",
            help="Sequence of angle ranges, in degrees.",
            default="40 20 10 5",
        )
        form.addParam(
            "steps",
            params.StringParam,
            label="Steps",
            help="Number of steps in the range to create the discretization",
            default="10 10 10 10",
        )
        form.addParam(
            "N_axes",
            params.IntParam,
            default=25,
            label="N axes",
            expertLevel=params.LEVEL_ADVANCED,
            help="For the first iteration, number of axes for the discretization of the"
            "sphere.",
        )
        form.addParam(
            "N_rot",
            params.IntParam,
            default=20,
            label="N rot",
            expertLevel=params.LEVEL_ADVANCED,
            help="For the first iteration, number of rotation per axis for the"
            "discretization of the sphere.",
        )

    def _insertAllSteps(self):
        self.root_dir = os.path.abspath(self._getExtraPath("root"))
        self.outputDir = os.path.abspath(self._getExtraPath("working_dir"))
        self.psfPath = os.path.join(self.root_dir, "psf.ome.tiff")
        self.initial_volume_path = os.path.join(
            self.root_dir, "initial_volume.ome.tiff"
        )
        self.final_reconstruction = os.path.abspath(
            self._getExtraPath("final_reconstruction.tif")
        )
        self.final_poses = os.path.abspath(self._getExtraPath("final_poses.csv"))
        self._insertFunctionStep(self.prepareStep)
        self._insertFunctionStep(self.reconstructionStep)
        self._insertFunctionStep(self.createOutputStep)

    def prepareStep(self):
        # Image links for particles
        particles: SetOfParticles = self.inputParticles.get()
        channel = self.channel.get() if particles.getNumChannels() > 0 else None
        particles_paths, max_dim = save_particles_and_poses(
            self.root_dir, particles, channel=channel
        )

        # PSF Path
        psf: PSFModel = self.inputPSF.get()
        save_image(self.psfPath, psf, channel=channel)

        # Initial volume path
        initial_volume: Particle = self.initialVolume.get()
        if initial_volume:
            save_image(self.initial_volume_path, initial_volume, channel=channel)

        # Make isotropic
        vs = particles.getVoxelSize()
        if vs is None:
            raise RuntimeError("Input Particles don't have a voxel size.")

        input_paths = particles_paths + [self.psfPath]
        if initial_volume:
            input_paths += [self.initial_volume_path]
        args = ["-f", "isotropic_resample"]
        args += ["-i"] + input_paths
        folder_isotropic = os.path.abspath(self._getExtraPath("isotropic"))
        if not os.path.exists(folder_isotropic):
            os.makedirs(folder_isotropic, exist_ok=True)
        args += ["-o", f"{folder_isotropic}"]
        args += ["--spacing", f"{vs[1]}", f"{vs[0]}", f"{vs[0]}"]
        Plugin.runJob(self, Plugin.getSPFluoProgram(UTILS_MODULE), args=args)

        # Pad
        input_paths = [
            os.path.join(folder_isotropic, f) for f in os.listdir(folder_isotropic)
        ]
        if self.pad:
            max_dim = int(max_dim * (2**0.5)) + 1
        folder_resized = os.path.abspath(self._getExtraPath("isotropic_cropped"))
        if not os.path.exists(folder_resized):
            os.makedirs(folder_resized, exist_ok=True)
        args = ["-f", "resize"]
        args += ["-i"] + input_paths
        args += ["--size", f"{max_dim}"]
        args += ["-o", f"{folder_resized}"]
        Plugin.runJob(self, Plugin.getSPFluoProgram(UTILS_MODULE), args=args)

        # Links
        os.remove(self.psfPath)
        for p in particles_paths:
            os.remove(p)
        # Link to psf
        os.link(
            os.path.join(folder_resized, os.path.basename(self.psfPath)), self.psfPath
        )
        # link to initial volume
        if initial_volume:
            os.remove(self.initial_volume_path)
            os.link(
                os.path.join(
                    folder_resized, os.path.basename(self.initial_volume_path)
                ),
                self.initial_volume_path,
            )
        # Links to particles
        for p in particles_paths:
            os.link(os.path.join(folder_resized, os.path.basename(p)), p)

    def reconstructionStep(self):
        ranges = "0 " + str(self.ranges) if len(str(self.ranges)) > 0 else "0"
        args = []
        if self.initialVolume.get():
            args += ["--initial_volume_path", self.initial_volume_path]
        args += [
            "--particles_dir",
            os.path.join(self.root_dir, "particles"),
            "--psf_path",
            self.psfPath,
            "--guessed_poses_path",
            os.path.join(self.root_dir, "poses.csv"),
            "--ranges",
            *ranges.split(" "),
            "--steps",
            f"({self.N_axes},{self.N_rot})",
        ]
        if len(str(self.steps)) > 0:
            args += str(self.steps).split(" ")
        args += [
            "--output_reconstruction_path",
            self.final_reconstruction,
            "--output_poses_path",
            self.final_poses,
            "-l",
            self.lbda.get(),
            "--symmetry",
            self.sym.get(),
        ]
        if self.gpu:
            args += ["--gpu"]
            if self.minibatch.get() > 0:
                args += ["--minibatch", self.minibatch.get()]
        Plugin.runJob(self, Plugin.getSPFluoProgram(REFINEMENT_MODULE), args=args)

    def createOutputStep(self):
        # Output 1 : reconstruction Volume
        vs = min(self.inputParticles.get().getVoxelSize())
        reconstruction = AverageParticle.from_filename(
            self.final_reconstruction, num_channels=1, voxel_size=(vs, vs)
        )

        # Output 2 : particles rotated
        output_particles = self._createSetOfParticles()
        transforms = {img_id: t for t, img_id in read_poses(self.final_poses)}
        for particle in self.inputParticles.get():
            particle: Particle

            rotated_transform = transforms[
                "particles/" + particle.strId() + ".ome.tiff"
            ]  # new coords

            # New file (link to particle)
            rotated_particle_path = self._getExtraPath(particle.getBaseName())
            os.link(particle.getFileName(), rotated_particle_path)

            # Creating the particle
            rotated_particle = Particle.from_filename(
                rotated_particle_path, voxel_size=particle.getVoxelSize()
            )
            rotated_particle.setTransform(rotated_transform)
            rotated_particle.setImageName(particle.getImageName())
            rotated_particle.setImgId(os.path.basename(rotated_particle_path))

            output_particles.append(rotated_particle)

        output_particles.write()

        self._defineOutputs(
            **{
                outputs.reconstructedVolume.name: reconstruction,
                outputs.particles.name: output_particles,
            }
        )
