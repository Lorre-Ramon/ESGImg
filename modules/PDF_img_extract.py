from utils import logger

import os 
import io
from PIL import Image, ImageOps 
import numpy as np
import pandas as pd 
import pymupdf 
from skimage import feature, color, exposure 
from typing import List

class PDFExtract: 
    def __init__(self, pdf_path:str)->None: 
        self.pdf_path = pdf_path 
        self.pdf = fitz.open(pdf_path)
        self.pdf_info = self.pdf.metadata
        self.pdf_page_count = self.pdf.page_count
        self.pdf_file_name = os.path.basename(pdf_path)
        
    def main(self) -> None: 
        pass 
    
    def createImgFolder(self) -> None: 
        """创建图片文件夹"""
        folder_path = os.path.join(os.path.dirname(self.pdf_path), f"{self.pdf_file_name.split('-')[0]}_img")
        os.makedirs(folder_path, exist_ok=True)
        
    def extractImg(self, page_num:int)->List[Image.Image]: 
        """提取PDF某页的全部图片

        Args:
            page_num (int): PDF页码

        Returns:
            List[Image.Image]: 图片列表
        """
        return self.pdf[page_num].get_images(full=True)

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
    
    def isBrightness(self, img, brightness_threshold:float = 0.75)->bool: 
        """亮度分布检测
        通过计算图像中明亮像素（灰度值大于128）的比例，来判断图像的亮度分布情况

        Args:
            img (_type_): 处理的图像
            brightness_threshold (float): 比例阈值. Defaults to 0.75.

        Returns:
            bool: True为图片为反色，False为正常
        """
        img_gray = img.convert('L')
        img_gray_np: np.ndarray = np.array(img_gray)
        
        light_fraction = np.mean(img_gray_np > 128)
        brightness_flag:bool = light_fraction > brightness_threshold 
        
        return brightness_flag
    

        