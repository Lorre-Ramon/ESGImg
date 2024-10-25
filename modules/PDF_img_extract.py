import os 
import io
from PIL import Image, ImageOps 
import numpy as np
import pandas as pd 
import fitz 
from skimage import feature, color, exposure 

class PDFImageFeatureDetect: 
    def __init__(self, img)->None:
        self.img = img
    
    def isImageInverted(self, img)->bool:
        """判断图片是否反色的main函数

        Args:
            img (_type_): 传入的图片

        Returns:
            bool: True为反色，False为正常
        """
        pass 
    
    def isBrightness(self, img, brightness_threshold)->bool: 
        
        img_gray = img.convert('L')
        img_gray_np: np.ndarray = np.array(img_gray)
        
        light_fraction = np.mean(img_gray_np > 128)
        brightness_flag:bool = light_fraction > brightness_threshold