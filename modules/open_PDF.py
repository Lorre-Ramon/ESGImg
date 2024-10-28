from utils import logger

import os 
import json
import pymupdf
import shutil

class OpenPDF: 
    def __init__(self, pdf_path:str, global_config_name:str)->None: 
        self.pdf_path = pdf_path 
        self.pdf_filename = os.path.basename(pdf_path)
        
        # configs 
        with open("configs/global_configs.json", "r") as f:
            global_configs = json.load(f)
            
        self.global_config = global_configs[global_config_name]
        
    def __enter__(self):
        self.pdf = pymupdf.open(self.pdf_path)
        logger.info(f"pdf: {self.pdf_filename}打开成功")
        self.pdf_page_count = self.pdf.page_count
        
        self.img_folder_path = self.createImgFolder() 
        logger.info(f"pdf: {self.pdf_filename}图片文件夹创建成功")
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pdf.close()
        logger.info(f"pdf: {self.pdf_filename}关闭，计算结束")
        
        self.deleteImgFolder()
        logger.info(f"pdf: {self.pdf_filename}图片文件夹删除成功")
        
    def createImgFolder(self) -> str: 
        """创建图片文件夹
        
        Raises:
            e: Anomaly exception for debugging
        
        Returns:
            str: 图片文件夹路径
        """
        try:
            folder_path = os.path.join(os.path.dirname(self.pdf_path), f"{self.pdf_filename.split('-')[0]}_img")
            os.makedirs(folder_path, exist_ok=True)
            return folder_path
        except Exception as e: 
            logger.BUG(f"Error: {e}\n\tpdf: {self.pdf_filename}取消创建图片文件夹")
            raise e
            # return ""
        
    def deleteImgFolder(self) -> None: 
        """删除图片文件夹

        Raises:
            e: Anomaly exception for debugging
        """
        try: 
            if os.path.exists(self.img_folder_path): 
                shutil.rmtree(self.img_folder_path)
                logger.info(f"pdf: {self.pdf_filename}图片文件夹删除")
            else:
                logger.error(f"pdf: {self.pdf_filename}图片文件夹不存在")
        except Exception as e: 
            logger.BUG(f"Error: {e}\n\tpdf: {self.pdf_filename}图片文件夹删除失败")
            raise e 