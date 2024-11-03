from utils import logger
from modules import OpenPDF

import os 
import pandas as pd 
import pymupdf
import pdb 
from dataclasses import dataclass
from typing import Tuple, List, Any

import warnings 
warnings.filterwarnings("ignore")

@dataclass
class PDFTextBlock: 
    pdf_filename: str
    pdf_page: int
    pdf_page_height: float
    text_index: int
    # img_info: Tuple[int,int,int,int,int,str,str,str,str,int]
    # img_bytes: bytes = None 
    # img_xref: str = None 
    # base_img: dict = None 
    # img_lazy_open: Image.Image = None 
    x0: int = None 
    y0: int = None 
    x1: int = None 
    y1: int = None 
    center_coord: Tuple[int,int] = None
    
class PDFTextExtract: 
    def __init__(self, pdf_instance: OpenPDF) -> None:
        """初始化PDFTextExtract类

        Args:
            pdf_instance (OpenPDF): 打开的PDF实例
        """
        self.pdf = pdf_instance
        
    def __post_init__(self) -> None:
        """__init__函数的后处理函数"""
        pass 
    
    def main(self) -> None: 
        """主函数"""
        pass 
    
    def extractTextListInfo(self, page_num: int) -> List[Tuple[float, float, float, float, str, Any, Any]]: 
        """提取PDF中某页的全部文本段信息

        Args:
            page_num (int): PDF的某页页数

        Raises:
            e: Anomaly exception for debugging

        Returns:
            List: 每个文本段的详细信息
                List[n][0]: block_x0: 文本段左上角x坐标
                List[n][1]: block_y0: 文本段左上角y坐标
                List[n][2]: block_x1: 文本段右下角x坐标
                List[n][3]: block_y1: 文本段右下角y坐标
                List[n][4]: block_text: 文本段内容
                List[n][5:]: 其他
        """
        try:
            page = self.pdf.pdf[page_num] 
            # retrieve the page's text in blocks
            blocks = page.get_text("blocks") 
            return blocks
        except Exception as e: 
            logger.error(f"pdf: {self.pdf.pdf_filename} page: {page_num} 文本段提取失败")
            logger.error(e)
            raise e 
            return []
        
    def extractTextInfo(self, block:List): 
        
        match block: 
            case _ if "<image:" in block[4]: 
                logger.info(f"pdf: {self.pdf.pdf_filename} page: {block[0]} text: {block[4]}为图像信息块，忽略")
            
        