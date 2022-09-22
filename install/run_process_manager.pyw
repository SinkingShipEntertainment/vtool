# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import sys
import os

parent_path = os.path.dirname(__file__)
vtool_path = os.path.dirname(parent_path)
vtool_path = os.path.join(vtool_path, 'python')

sys.path.append( vtool_path )

from vtool import qt_ui
from vtool import util
from vtool.process_manager import ui_process_manager

def main(directory = None):
    
    window = None
    
    from vtool import logger
    logger.setup_logging(level = 'DEBUG')
    
    if not util.is_in_maya():
        window = ui_process_manager.ProcessManagerWindow()  
        window.show()
        
        return window
        
    if util.is_in_maya():
        from vtool.maya_lib import ui
        ui.process_manager()
        
if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    window = main()
    
    sys.exit(APP.exec_())