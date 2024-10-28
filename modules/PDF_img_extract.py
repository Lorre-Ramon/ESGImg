from utils import logger
from modules import OpenPDF

import os 
import io
from PIL import Image, ImageOps 
import numpy as np
import pandas as pd 
import pymupdf 
from skimage import feature, color, exposure 
from typing import List, Tuple
from dataclasses import dataclass

@dataclass 
class PDFImage:
    pdf_filename: str
    pdf_page: int
    img_index: int
    img_folderpath: str
    img_filename: str
    img_info: Tuple[int,int,int,int,int,str,str,str,str,int]
    img_bytes: bytes 
    img_xref: str
    base_img: dict
    x0: int 
    y0: int 
    x1: int
    y1: int
    center_coord: Tuple[int,int]

class PDFImgExtract(OpenPDF): 
    def __init__(self)->None: 
        super().__init__()
        
    def main(self) -> pd.DataFrame: 
        
        logger.info(f"pdf: {self.pdf_filename}开始提取图片")
        successful_img_cnt = 0
        coords_df:pd.DataFrame = pd.DataFrame(columns=["file_name", "x0", "y0", "x1", "y1", 
                                          "centre_coordinate"])
        # 遍历PDF每一页
        for page_num in range(self.pdf_page_count): 
            img_list = self.extractImgInfoList(page_num)
            page = self.pdf[page_num]
            # 遍历每一页的图片
            for img_index, img_info in enumerate(img_list): 
                img_filename = f"{self.pdf_filename}_page_{page_num + 1}_img_{img_index + 1}.png"
                img = PDFImage(self.pdf_filename, page_num, img_index, 
                               self.img_folder_path,
                               img_filename, img_info)
                
                self.extractImgInfo(page, page_num, img_index, img_info)
                
                if abs(img.x0 - img.x1) < 50 or abs(img.y0 - img.y1) < 50: 
                    logger.warning(f"pdf: {self.pdf_filename}, page_num: {page_num}, img_index: {img_index}\
                                \n\t图片尺寸过小, 取消提取")
                    continue
                
                #TODO: 图片反色检测
                
                self.extractImgCoord(page, img)
                info = pd.Series([img.img_filename, 
                                  img.x0, img.y0, img.x1, img.y1, 
                                  img.center_coord], 
                                 index=coords_df.columns)
                coords_df = pd.concat([coords_df, info], axis=0)
                
                self.saveImg(img)
                
                successful_img_cnt += 1
        
        if successful_img_cnt < len(self.pdf) + self.global_config["successful_img_cnt_buffer"]: 
            logger.warning(f"pdf: {self.pdf_filename}提取图片数量过少, 数量: {successful_img_cnt}")
           
        return coords_df
    
    
        
    def extractImgInfoList(self, page_num:int)->List[Tuple[int,int,int,int,int,str,str,str,str,int]]: 
        """提取PDF某页的全部图片Xref信息

        Args:
            page_num (int): PDF页码

        Returns:
            List[Tuple[int,int,int,int,int,str,str,str,str,int]]: 图片列表 #FIXME: 这里列表内容的含义不明
            	•	int, int: 图像在页面上的位置(X 和 Y 坐标)
                •	int, int: 图像的宽度和高度
                •	int: 位深度
                •	str: 颜色空间
                •	str: 透明度或遮罩信息(可能为空字符串)
                •	str: 图像 ID
                •	str: 编码类型。
                •	int: 额外编码参数
        """
        try: 
            return self.pdf[page_num].get_images(full=True)
        except Exception as e: 
            logger.error(f"pdf: {self.pdf_filename}, page_num: {page_num}\n\t取消提取图片信息Error: {e}")
            return []
    
    def extractImgInfo(self, img:PDFImage) -> None: 
        """提取图像xref, 图像字节信息

        Args:
            img (PDFImage): 处理的当前图片
        """
        try: 
            img.img_xref = img.img_info[0]
            img.base_img = self.pdf.extract_image(img.img_xref)
            
            match img.base_img:
                case dict():
                    img.img_bytes = img.base_img['image'] 
                case __:
                    logger.bug(f"pdf: {self.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                                \n\tError: img类型非dict")
                    raise TypeError("img类型非dict")
        except Exception as e:
            logger.error(f"pdf: {self.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\tError: {e}")
        
    def extractImgCoord(self, page:pymupdf.Page, img:PDFImage)->None: 
        """提取图片坐标信息

        Args:
            page (pymupdf.Page): PDF当前页
            img (PDFImage): 处理的当前图片
        """
        try: 
            img_xref = img.img_info[0]
            image_rect = page.get_image_rect(img_xref)
            rect = image_rect[0]
            img.x0, img.y0, img.x1, img.y1 = rect.x0, rect.y0, rect.x1, rect.y1
            img.center_coord = (img.x0 + img.x1)/2 , (img.y0 + img.y1)/2
        except not image_rect: 
            logger.error(f"pdf: {self.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\tError: Cannot get image rectangle for xref {img_xref}")
            image_rect = None
            img.x0, img.y0, img.x1, img.y1 = None, None, None, None
            img.center_coord = None
        except Exception as e:
            logger.bug(f"pdf: {self.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\tUnexpected BUG: {e}")
            raise e
            
    def saveImg(self, img:PDFImage)->None:
        """保存图片

        Args:
            img (PDFImage): 图片信息dataclass
        """
        try: 
            image = Image.open(io.BytesIO(img.img_bytes))
            image_filepath = os.path.join(img.img_folderpath, img.img_filename)
            image.save(open(image_filepath, "wb"), "PNG")
        except Image.DecompressionBombError as e:
            logger.error(f"pdf: {self.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t检测到过大图片,取消保存: {e}")
        except Exception as e: 
            logger.error(f"pdf: {self.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t保存图片失败: {e}")
            
                                
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
    
    def isBright(self, img, brightness_threshold:float = 0.75) -> bool: 
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
    
    def compareColorHistogram(self, threshold:float = 0.8) -> bool:
        pass 
    
    def detectEdge(self, img, edge_threshold:float = 0.1) -> bool: 
        """边缘检测
        通过计算图像中边缘像素的比例，来判断图像是否为边缘图像

        Args:
            img (_type_): 处理的图像
            edge_threshold (float): 比例阈值. Defaults to 0.1.

        Returns:
            bool: True为图片为反色，False为正常
        """
        img_gray = img.convert('L')
        img_gray_np: np.ndarray = np.array(img_gray)
        
        edges = feature.canny(img_gray_np)
        edge_fraction = np.mean(edges)
        edge_flag:bool = edge_fraction > edge_threshold
        
        return edge_flag
    

        