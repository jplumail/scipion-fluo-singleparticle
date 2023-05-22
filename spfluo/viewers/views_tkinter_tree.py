from typing import List, Optional, Tuple
from pyworkflow.gui.dialog import ToolbarListDialog
from pyworkflow.gui.tree import TreeProvider
import pyworkflow.utils as pwutils
from pyworkflow.viewer import View
from pyworkflow.protocol import Protocol

import os
import glob
import threading

from spfluo.objects.data import FluoImage


class FluoImagesTreeProvider(TreeProvider):
    """ Populate Tree from SetOfFluoImages. """

    def __init__(self, protocol: Protocol, fluoimagesList: List[FluoImage]):
        TreeProvider.__init__(self)
        self.protocol: Protocol = protocol
        self.fluoimagesList: List[FluoImage] = fluoimagesList

    def getColumns(self):
        return [('FluoImage', 300), ("# coords", 100), ('status', 150)]
    
    def getCsvPath(self, im: FluoImage) -> Tuple[str, str]:
        """ Get the FluoImage path and its csv file path"""
        path = im.getFileName()
        if path is None:
            raise Exception(f"{im} file path is None! Cannot launch napari.")
        path = os.path.abspath(path)
        fname, _ = os.path.splitext(os.path.basename(path))
        csv_file = fname + '.csv'
        csv_path = os.path.abspath(self.protocol._getExtraPath(csv_file))
        return path, csv_path

    def getObjectInfo(self, im: FluoImage) -> Optional[dict]:
        path, csv_path = self.getCsvPath(im)
        im_name, _ = os.path.splitext(os.path.basename(path))
        d = {'key': im_name, 'parent': None, 'text': im_name}
        if im.in_viewer:
            status_text = "IN PROGRESS"
            d['tags'] = ("in progress")
        elif im.count > 0:
            status_text = "DONE"
            d['tags'] = ("done")
        else:
            status_text = "TODO"
            d['tags'] = ("pending")
        d['values'] = (im.count, status_text)
        return d

    def getObjectPreview(self, obj):
        return (None, None)

    def getObjectActions(self, obj):
        return []

    def _getObjectList(self):
        """Retrieve the object list"""
        return self.fluoimagesList

    def getObjects(self):
        objList = self._getObjectList()
        return objList

    def configureTags(self, tree):
        tree.tag_configure("pending", foreground="red")
        tree.tag_configure("done", foreground="green")
        tree.tag_configure("in progress", foreground="black")


class NapariDialog(ToolbarListDialog):
    """
    taken from scipion-em-emantomo/emantomo/viewers/views_tkinter_tree.py:EmanDialog
    This class extend from ListDialog to allow calling
    a Napari subprocess from a list of FluoImages.
    """

    def __init__(self, parent, provider: FluoImagesTreeProvider, **kwargs):
        self.provider = provider
        ToolbarListDialog.__init__(self, parent,
                                   "Fluoimage List",
                                   self.provider,
                                   allowsEmptySelection=False,
                                   itemDoubleClick=self.doubleClickOnFluoimage,
                                   allowSelect=False,
                                   **kwargs)

    def refresh_gui(self):
        for im in self.provider.fluoimagesList:
            _, csv_path = self.provider.getCsvPath(im)
            if os.path.isfile(csv_path):
                # count number of lines in csv file
                with open(csv_path, 'r') as f:
                    count = sum(1 for line in f)
                if count > 0:
                    im.count = count - 1
        if not self.proc.is_alive():
            self.fluoimage.in_viewer = False
        self.tree.update()
        self.after(1000, self.refresh_gui)

    def doubleClickOnFluoimage(self, e=None):
        self.fluoimage = e
        self.fluoimage.in_viewer = True
        self.proc = threading.Thread(target=self.lanchNapariForFluoImage, args=(self.fluoimage,))
        self.proc.start()
        self.after(1000, self.refresh_gui)

    def lanchNapariForFluoImage(self, im: FluoImage):
        from spfluo import Plugin
        from spfluo.constants import MANUAL_PICKING_MODULE
        path, csv_path = self.provider.getCsvPath(im)
        args = " ".join([path, csv_path])
        Plugin.runSPFluo(self.provider.protocol, Plugin.getProgram(MANUAL_PICKING_MODULE), args)

    def _moveCoordsToInfo(self, tomo):
        fnCoor = '*%s_info.json' % pwutils.removeBaseExt(tomo.getFileName().split("__")[0])
        pattern = os.path.join(self.path, fnCoor)
        files = glob.glob(pattern)

        if files:
            infoDir = pwutils.join(os.path.abspath(self.path), 'info')
            pathCoor = os.path.join(infoDir, os.path.basename(files[0]))
            pwutils.makePath(infoDir)
            copyFile(files[0], pathCoor)


class NapariView(View):
    """ This class implements a view using Tkinter ListDialog
    and the FluoImagesTreeProvider.
    """

    def __init__(self, parent, protocol: Protocol, fluoList: List[FluoImage], **kwargs):
        self._tkParent = parent
        self._protocol = protocol
        self._provider = FluoImagesTreeProvider(protocol, fluoList)

    def show(self):
        NapariDialog(self._tkParent, self._provider)