from utils import logger

import os 
import json
import pymupdf
import shutil
from dataclasses import dataclass

@dataclass
class OpenPDF: 
    pdf_path: str 
    global_config_name:str
    
    def __post_init__(self)->None: 
        """__init__函数的后处理函数"""
        # configs 
        with open("configs/global_configs.json", "r") as f:
            global_configs = json.load(f)
        self.global_config = global_configs[self.global_config_name]
        
        # Basic Info
        self.getBasicInfo()
        
    def getBasicInfo(self) -> None: 
        """获取PDF文件的基本信息"""
        self.year:int = int(self.pdf_path.split("/")[2])
        self.type:str = self.pdf_path.split("/")[1]
        self.thscode:str = self.pdf_path.split("/")[-1].split("-")[0]
        self.stock_name_cn:str = self.pdf_path.split("/")[-1].split("-")[1]
        self.PDF_name:str = self.pdf_path.split("/")[-1].split("-")[2]
        
        self.pdf_filename:str = f"{self.type}_{self.year}_{self.thscode}_{self.stock_name_cn}.pdf"
        
    def __enter__(self) -> "OpenPDF":
        """__enter__函数

        Returns:
            OpenPDF: 返回OpenPDF实例
        """
        self.pdf = pymupdf.open(self.pdf_path)
        logger.info(f"pdf: {self.pdf_filename}打开成功")
        self.pdf_page_count = self.pdf.page_count
        
        self.img_folder_path = self.createImgFolder() 
        logger.info(f"pdf: {self.pdf_filename}图片文件夹创建成功")
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.pdf.close()
        logger.info(f"pdf: {self.pdf_filename}关闭，计算结束")
        
        self.deleteImgFolder(self.img_folder_path)
        
    def createImgFolder(self) -> str: 
        """创建图片文件夹
        
        Raises:
            e: Anomaly exception for debugging
        
        Returns:
            str: 图片文件夹路径
        """
        try:
            folder_path = os.path.join("output", f"{self.pdf_filename.split('-')[0]}_img")
            os.makedirs(folder_path, exist_ok=True)
            return folder_path
        except Exception as e: 
            logger.BUG(f"Error: {e}\n\tpdf: {self.pdf_filename}取消创建图片文件夹")
            raise e
            # return ""
        
    def deleteImgFolder(self, img_folder_path:str) -> None: 
        """删除图片文件夹

        Raises:
            e: Anomaly exception for debugging
        """
        try: 
            if os.path.exists(img_folder_path): 
                shutil.rmtree(img_folder_path)
                logger.info(f"{self.pdf_filename}图片文件夹删除")
            else:
                logger.error(f"{self.pdf_filename}图片文件夹不存在")
        except Exception as e: 
            logger.BUG(f"Error: {e}\n\t{self.pdf_filename}图片文件夹删除失败")
            raise e 
        
    def getPDFImgExtract(self) -> "PDFImgExtract": 
        """返回提取图片的子类实例

        Returns:
            PDFImgExtract: 提取图片的子类实例
        """
        from .PDF_img_extract import PDFImgExtract
        return PDFImgExtract(self)
    
    def getPDFTextExtract(self) -> "PDFTextExtract": 
        """返回提取文本的子类实例

        Returns:
            PDFTextExtract: 提取文本的子类实例
        """
        from .PDF_text_extract import PDFTextExtract
        return PDFTextExtract(self)