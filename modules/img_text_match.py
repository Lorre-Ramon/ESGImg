import jiagu
import string 
import numpy as np
import pandas as pd
import torch
import itertools
import re 
import os
import pymupdf
import ast 
import math 

from PIL import Image

import cn_clip.clip as clip
from cn_clip.clip import load_from_name, available_models
# print("Available models:", available_models())  