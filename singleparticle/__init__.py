# **************************************************************************
# *
# * Authors:     Jean Plumail (jplumail@unistra.fr)
# *
# * ICube, University of Strasburg
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os
from typing import List, Optional, Union

import pyworkflow as pw
import pyworkflow.utils as pwutils
import spfluo
from pwfluo.objects import FluoObject
from pyworkflow import plugin
from pyworkflow.protocol import Protocol
from pyworkflow.utils import getSubclasses
from pyworkflow.viewer import Viewer
from pyworkflow.wizard import Wizard

from singleparticle.constants import (
    FLUO_ROOT_VAR,
    SINGLEPARTICLE_HOME,
)

_logo = "icon.png"
_references = ["Fortun2017"]


class Config(pw.Config):
    _get = pw.Config._get
    _join = pw.Config._join

    FLUO_ROOT = _join(_get(FLUO_ROOT_VAR, _join(pw.Config.SCIPION_SOFTWARE, "fluo")))


class Domain(plugin.Domain):
    _name = __name__
    _objectClass = FluoObject
    _protocolClass = Protocol
    _viewerClass = Viewer
    _wizardClass = Wizard
    _baseClasses = getSubclasses(FluoObject, globals())


class Plugin(plugin.Plugin):
    _homeVar = SINGLEPARTICLE_HOME

    @classmethod
    def getDependencies(cls):
        """Return a list of dependencies. Include conda if
        activation command was not found."""
        return []

    @classmethod
    def getEnviron(cls):
        """Setup the environment variables needed to launch Relion."""
        environ = pwutils.Environ(os.environ)

        return environ

    @classmethod
    def runSPFluo(cls, protocol: Protocol, program, args, cwd=None, useCpu=False):
        """Run SPFluo command from a given protocol."""
        protocol.runJob(
            program,
            args,
            env=cls.getEnviron(),
            cwd=cwd,
            numberOfMpi=1,
        )

    @classmethod
    def getProgram(cls, program: Union[str, List[str]]):
        if type(program) is str:
            program = [program]
        command = "python -m spfluo"
        for p in program:
            command += f".{p}"
        return command

    @classmethod
    def getNapariProgram(cls, plugin: Optional[str] = "napari-aicsimageio"):
        napari_cmd = "python -m napari"
        if plugin:
            napari_cmd += f" --plugin {plugin}"
        return napari_cmd

    @classmethod
    def addSingleParticlePackage(cls, env):
        env.addPackage(
            "singleparticle",
            version=spfluo.__version__,
            tar="void.tgz",
            commands=[],
            neededProgs=cls.getDependencies(),
            default=True,
            vars=None,
        )

    @classmethod
    def defineBinaries(cls, env):
        cls.addSingleParticlePackage(env)