#!/usr/bin/env python3

from collections import defaultdict
from collections import OrderedDict
from lib import *
from lib.utils import *
from lib.processor import *
from lib.ui import *
import tkinter as tk
import datetime
import glob
import importlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
# hot-loaded if needed, see import_module():
#  imagesize
#  requests


# Print a compile-time error in Python < 3.6. This line does nothing in Python 3.6+ but is reported to the user
# as an error (because it is the first line that fails to compile) in older versions.
f' Error: This script requires Python 3.6 or later.'

if __name__=='__main__':
    processor = Processor('../..')
    main_window = MainWindow(processor)
    main_window.show()    