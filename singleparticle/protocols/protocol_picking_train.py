# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************


"""
Describe your python module here:
This module will provide the traditional Hello world example
"""
import os
import random

from pwfluo.objects import SetOfCoordinates3D
from pyworkflow import BETA
from pyworkflow.protocol import Protocol, params

from singleparticle import Plugin
from singleparticle.constants import PICKING_MODULE, PICKING_WORKING_DIR
from singleparticle.convert import write_csv


class ProtSingleParticlePickingTrain(Protocol):
    """
    Picking for fluo data with deep learning
    """

    _label = "picking train"
    _devStatus = BETA

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        form.addSection(label="Data params")
        group = form.addGroup("Input")
        group.addParam(
            "inputCoordinates",
            params.PointerParam,
            pointerClass="SetOfCoordinates3D",
            label="Annotations 3D coordinates",
            important=True,
        )
        form.addParam(
            "pu",
            params.BooleanParam,
            label="Positive Unlabelled learning",
            default=True,
            expertLevel=params.LEVEL_ADVANCED,
        )
        group = form.addGroup("PU params", condition="pu")
        group.addParam(
            "num_particles_per_image",
            params.IntParam,
            default=None,
            condition="pu",
            label="Number of particles per image",
        )
        group.addParam(
            "radius",
            params.IntParam,
            default=None,
            condition="pu",
            label="Radius",
            expertLevel=params.LEVEL_ADVANCED,
            allowsNull=True,
        )
        form.addSection(label="Advanced", expertLevel=params.LEVEL_ADVANCED)
        form.addParam(
            "lr",
            params.FloatParam,
            label="Learning rate",
            default=1e-3,
        )
        group = form.addGroup("Data params")
        group.addParam(
            "train_val_split",
            params.FloatParam,
            default=0.7,
            label="Train/val split",
            help="By default 70% of the data is in the training set",
        )
        group.addParam(
            "batch_size",
            params.IntParam,
            label="Batch size",
            default=128,
        )
        group.addParam(
            "epoch_size",
            params.IntParam,
            label="epoch size",
            default=20,
        )
        group.addParam(
            "num_epochs",
            params.IntParam,
            label="num epochs",
            default=5,
        )
        group.addParam(
            "shuffle",
            params.BooleanParam,
            label="Shuffle samples at each epoch",
            default=True,
        )
        group.addParam(
            "augment",
            params.FloatParam,
            label="Augment rate",
            default=0.8,
        )
        # SWA
        form.addParam(
            "swa",
            params.BooleanParam,
            label="Enable SWA",
            default=True,
            help="Stochastic Weight Averaging",
            expertLevel=params.LEVEL_ADVANCED,
        )
        group = form.addGroup("SWA params", condition="swa")
        group.addParam(
            "swa_lr",
            params.FloatParam,
            condition="swa",
            label="SWA learning rate",
            default=1e-5,
            expertLevel=params.LEVEL_ADVANCED,
        )

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        self.pickingPath = os.path.abspath(self._getExtraPath(PICKING_WORKING_DIR))
        self.rootDir = os.path.join(self.pickingPath, "rootdir")
        self._insertFunctionStep(self.prepareStep)
        self._insertFunctionStep(self.trainStep)

    def prepareStep(self):
        if not os.path.exists(self.rootDir):
            os.makedirs(self.rootDir, exist_ok=True)
        os.makedirs(os.path.join(self.rootDir, "train"), exist_ok=True)
        os.makedirs(os.path.join(self.rootDir, "val"), exist_ok=True)

        # Image links
        inputCoordinates: SetOfCoordinates3D = self.inputCoordinates.get()
        images = set(
            [coord.getFluoImage() for coord in inputCoordinates.iterCoordinates()]
        )
        for im in images:
            im_path = os.path.abspath(im.getFileName())
            ext = os.path.splitext(im_path)[1]
            im_name = im.getImgId()
            im_newPath = os.path.join(self.rootDir, im_name + ".tif")
            if ext != ".tif" and ext != ".tiff":
                raise NotImplementedError(
                    f"Found ext {ext} in particles: {im_path}. "
                    "Only tiff file are supported."
                )  # FIXME: allow formats accepted by AICSImageio
            else:
                if not os.path.exists(im_newPath):
                    print(f"Link {im_path} -> {im_newPath}")
                    os.link(im_path, im_newPath)
            for s in ["train", "val"]:
                im_newPathSet = os.path.join(self.rootDir, s, im_name + ".tif")
                if not os.path.exists(im_newPathSet):
                    print(f"Link {im_newPath} -> {im_newPathSet}")
                    os.link(im_newPath, im_newPathSet)

        # Splitting annotations in train/val
        annotations = []
        for i, coord in enumerate(inputCoordinates.iterCoordinates()):
            x, y, z = coord.getPosition()
            annotations.append((coord.getFluoImage().getImgId() + ".tif", i, x, y, z))

        print(
            f"Found {len(annotations)} annotations in SetOfCoordinates "
            f"created at {inputCoordinates.getObjCreationAsDate()}"
        )
        random.shuffle(annotations)
        i = int(self.train_val_split.get() * len(annotations))
        train_annotations, val_annotations = annotations[:i], annotations[i:]

        # Write CSV
        write_csv(
            os.path.join(self.rootDir, "train", "train_coordinates.csv"),
            train_annotations,
        )
        write_csv(
            os.path.join(self.rootDir, "val", "val_coordinates.csv"), val_annotations
        )

        # Prepare stage
        ps = inputCoordinates.getBoxSize()
        args = ["--stages", "prepare"]
        args += ["--rootdir", f"{self.rootDir}"]
        args += ["--extension", "tif"]
        args += ["--crop_output_dir", "cropped"]
        args += ["--make_u_masks"]
        args += ["--patch_size", f"{ps}"]
        Plugin.runJob(self, Plugin.getSPFluoProgram(PICKING_MODULE), args=args)

    def trainStep(self):
        inputCoordinates: SetOfCoordinates3D = self.inputCoordinates.get()
        ps = inputCoordinates.getBoxSize()
        args = ["--stages", "train"]
        args += ["--batch_size", f"{self.batch_size.get()}"]
        args += ["--rootdir", f"{self.rootDir}"]
        args += ["--output_dir", f"{self.pickingPath}"]
        args += ["--patch_size", f"{ps}"]
        args += ["--epoch_size", f"{self.epoch_size.get()}"]
        args += ["--num_epochs", f"{self.num_epochs.get()}"]
        args += ["--lr", f"{self.lr.get()}"]
        args += ["--extension", "tif"]
        args += ["--augment", f"{self.augment.get()}"]
        if self.pu:
            args += ["--mode", "pu"]
            if self.radius.get() is None:
                args += ["--radius", f"{ps//2}"]
                args += ["--load_u_masks"]
            else:
                args += ["--radius", f"{self.radius.get()}"]
            args += [
                "--num_particles_per_image",
                f"{self.num_particles_per_image.get()}",
            ]
        else:
            args += ["--mode", "fs"]
        if self.shuffle.get():
            args += ["--shuffle"]
        if self.swa.get():
            args += ["--swa", "--swa_lr", f"{self.swa_lr.get()}"]
        Plugin.runJob(self, Plugin.getSPFluoProgram(PICKING_MODULE), args=args)

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("Protocol is finished")
        return summary

    def _methods(self):
        methods = []
        return methods
