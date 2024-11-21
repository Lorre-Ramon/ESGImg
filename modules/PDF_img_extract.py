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

import warnings
warnings.filterwarnings("ignore")

@dataclass 
class PDFImage:
    pdf_filename: str
    pdf_page: int
    img_index: int
    img_folderpath: str
    img_filename: str
    img_info: Tuple[int,int,int,int,int,str,str,str,str,int]
    img_bytes: bytes = None 
    img_xref: str = None 
    base_img: dict = None 
    img_lazy_open: Image.Image = None 
    x0: int = None 
    y0: int = None 
    x1: int = None 
    y1: int = None 
    center_coord: Tuple[int,int] = None 

class PDFImgExtract: 
    def __init__(self, pdf_instance:OpenPDF) -> None: 
        """初始化PDFImgExtract类
        
        Args: 
            pdf_instance (OpenPDF): 打开的PDF实例
        """
        self.pdf:OpenPDF = pdf_instance
        
    def __post_init__(self) -> None: 
        """__init__函数的后处理函数"""
        import json
        with open("configs/img_extract_configs.json", "r") as f:
            configs = json.load(f)
            
        self.img_extract_config = configs["img_extract"]
    
    def main(self) -> pd.DataFrame: 
        """PDF图片提取主函数

        Returns:
            pd.DataFrame: 返回当前和历史的PDF文件的图片坐标信息
        """
        successful_img_cnt = 0
        coords_df:pd.DataFrame = pd.DataFrame(columns=["file_name", "x0", "y0", "x1", "y1", 
                                          "centre_coordinate"])
        # 遍历PDF每一页
        for page_num in range(self.pdf.pdf_page_count): 
            img_list = self.extractImgInfoList(page_num)
            page = self.pdf.pdf[page_num]
            # 遍历每一页的图片
            for img_index, img_info in enumerate(img_list): 
                img_filename = f"{self.pdf.file_name_short}_page_{page_num + 1}_img_{img_index + 1}.png"
                img = PDFImage(self.pdf.file_name_short, page_num, img_index, 
                               self.pdf.img_folder_path,
                               img_filename, img_info)
                
                self.extractImgInfo(img)
                self.extractImgCoord(page, img)
                
                # if abs(img.x0 - img.x1) < 50 or abs(img.y0 - img.y1) < 50:  #TODO: 是否对长度添加限制
                if abs(img.x0 - img.x1) < self.pdf.global_config["img_height_threshold"]: 
                    logger.warning(f"pdf: {self.pdf.file_name_short}, page_num: {page_num}, img_index: {img_index}\
                                \n\t图片尺寸过小, 取消提取")
                    continue
                
                if self.pdf.global_config["detect_inverted_img"]: 
                    img_feature_detection = PDFImageFeatureDetection(img)
                    
                    if img_feature_detection.main(img): 
                        img.img_lazy_open = ImageOps.invert(img.img_lazy_open)
                        logger.warninfoing(f"pdf: {self.pdf.file_name_short}, page_num: {page_num}, img_index: {img_index}\
                                    \n\t图片反色, 进行反色处理")
                     
                info = pd.Series([img.img_filename, 
                                  img.x0, img.y0, img.x1, img.y1, 
                                  img.center_coord], 
                                 index=coords_df.columns)
                coords_df = pd.concat([coords_df, pd.DataFrame([info])], ignore_index=True)
                
                self.saveImg(img)
                
                successful_img_cnt += 1
        
        if successful_img_cnt < len(self.pdf.pdf) + self.pdf.global_config["successful_img_cnt_buffer"]: 
            logger.warning(f"pdf: {self.pdf.file_name_short}提取图片数量过少, 数量: {successful_img_cnt}")
        
        coords_df = self.tagOutput(coords_df)
        
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
            return self.pdf.pdf[page_num].get_images(full=True)
        except Exception as e: 
            logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {page_num}\n\t取消提取图片信息Error: {e}")
            return []
    
    def extractImgInfo(self, img:PDFImage) -> None: 
        """提取图像xref, 图像字节信息

        Args:
            img (PDFImage): 处理的当前图片
        """
        try: 
            img.img_xref = img.img_info[0]
            img.base_img = self.pdf.pdf.extract_image(img.img_xref)
            
            match img.base_img:
                case dict():
                    img.img_bytes = img.base_img['image'] 
                case __:
                    logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                                \n\tError: img类型非dict")
                    raise TypeError("img类型非dict")
                
            img.img_lazy_open = Image.open(io.BytesIO(img.img_bytes)) 
            if img.img_lazy_open.mode != "RGB": 
                img.img_lazy_open = img.img_lazy_open.convert("RGB")
        except Image.DecompressionBombError as e:
            logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t检测到过大图片,取消保存: {e}")
        except Exception as e:
            logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\tError: {e}")
        
    def extractImgCoord(self, page:pymupdf.Page, img:PDFImage)->None: 
        """提取图片坐标信息

        Args:
            page (pymupdf.Page): PDF当前页
            img (PDFImage): 处理的当前图片
        """
        try: 
            img_xref = img.img_info[0]
            image_rect = page.get_image_rects(img_xref)
            rect = image_rect[0]
            img.x0, img.y0, img.x1, img.y1 = rect.x0, rect.y0, rect.x1, rect.y1
            img.center_coord = (img.x0 + img.x1)/2 , (img.y0 + img.y1)/2
        except not page.get_image_rects(img_xref): 
            logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\tError: Cannot get image rectangle for xref {img_xref}")
            image_rect = None
            img.x0, img.y0, img.x1, img.y1 = None, None, None, None
            img.center_coord = None
        except Exception as e:
            logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\tUnexpected BUG: {e}")
            raise e
            
    def saveImg(self, img:PDFImage)->None:
        """保存图片

        Args:
            img (PDFImage): 图片信息dataclass
        """
        try: 
            image_filepath = os.path.join(img.img_folderpath, img.img_filename)
            img.img_lazy_open.save(open(image_filepath, "wb"), "PNG")
        except Exception as e: 
            logger.error(f"pdf: {self.pdf.file_name_short}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t保存图片失败: {e}")
            
    def tagOutput(self, df_img:pd.DataFrame) -> pd.DataFrame: 
        """标记输出信息

        Args:
            df_img (pd.DataFrame)

        Returns:
            pd.DataFrame: 标记后的输出信息
        """
        def extractPDFName(file_name):
            PDF_name, _, _, _, _ = file_name.split('_')
            return str(PDF_name) 
        
        def extractPageNum(file_name):
            _, _, page, _, _ = file_name.split('_')
            return int(page)

        def extractImgIndex(file_name):
            _, _, _, _, p_index = file_name.split('_')
            return int(p_index[:-4])
        
        df_img["PDF_name"] = df_img["file_name"].apply(extractPDFName)
        df_img["page"] = df_img["file_name"].apply(extractPageNum)
        df_img["p_index"] = df_img["file_name"].apply(extractImgIndex)
                
        return df_img
                                
class PDFImageFeatureDetection: 
    def __init__(self, img:PDFImage)->None:
        self.img = img
    
    def main(self, img:PDFImage)->bool:
        """判断图片是否反色的main函数

        Args:
            img (PDFImage): 图片

        Returns:
            bool: 投票后的结果. True为反色,False为正常
        """
        return sum([self.isBright(img), self.compareColorHistogram(img), self.detectEdge(img)]) > 2
    
    def isBright(self, img:PDFImage, brightness_threshold:float = 0.75) -> bool: 
        """亮度分布检测
        通过计算图像中明亮像素（灰度值大于128）的比例，来判断图像的亮度分布情况

        Args:
            img (PDFImage): 处理的图像
            brightness_threshold (float): 比例阈值. Defaults to 0.75.

        Returns:
            bool: True为图片为反色，False为正常
        """
        try:
            img2 = img.img_lazy_open
            img_gray = img2.convert('L')
            img_gray_np: np.ndarray = np.array(img_gray)
            
            light_fraction = np.mean(img_gray_np > 128)
            brightness_flag:bool = light_fraction > brightness_threshold 
            
            return brightness_flag
        except Exception as e:
            logger.error(f"pdf: {img.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t亮度分布检测失败: {e}")
            return False
    
    def compareColorHistogram(self, img:PDFImage, histogram_threshold:float = 0.8) -> bool:
        """颜色直方图比较 #TODO: 方法有效性存疑

        Args:
            img (PDFImage): 图片
            histogram_threshold (float, optional): 原始图与反色图的直方图相关系数阈值. Defaults to 0.8.

        Returns:
            bool: True为图片为反色，False为正常
        """
        img2 = img.img_lazy_open
        
        try:
            img2 = img2.convert("RGB")
            
            img_hist = exposure.histogram(np.array(img2.convert("RGB")), nbins=256)
            inverted_img_hist = exposure.histogram(np.array(ImageOps.invert(img2).convert("RGB")), nbins=256)
            hist_correlation = np.corrcoef(img_hist[0], inverted_img_hist[0])[0, 1]
            histogram_flag:bool = hist_correlation > histogram_threshold
            
            return histogram_flag
        except Exception as e:
            logger.error(f"pdf: {img.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t颜色直方图比较失败: {e}")
            return False
    
    def detectEdge(self, img:PDFImage, edge_threshold:float = 0.8) -> bool: 
        """边缘检测 #TODO: 方法有效性存疑
        使用边缘检测算法Canny来提取图像的边缘。然后，比较原始图像和其反色版本的边缘强度。
        使用相关系数来测量原始图像的边缘和其反色版本之间的边缘强度相似性。
        如果相关系数超过预设的边缘检测阈值，该方法将投票为“反色”。

        Args:
            img (PDFImage): 处理的图像
            edge_threshold (float): 比例阈值. Defaults to 0.8.

        Returns:
            bool: True为图片为反色，False为正常
        """
        try: 
            img2 = img.img_lazy_open
            img2 = img2.convert("RGB")
            
            edges_original = feature.canny(color.rgb2gray(np.array(img2)))
            edges_inverted = feature.canny(color.rgb2gray(np.array(ImageOps.invert(img2))))
            edge_correlation = np.corrcoef(edges_original.flatten(), edges_inverted.flatten())[0, 1]
            edge_flag = edge_correlation > edge_threshold
            
            return edge_flag
        except Exception as e:
            logger.error(f"pdf: {img.pdf_filename}, page_num: {img.pdf_page}, img_index: {img.img_index}\
                        \n\t边缘检测失败: {e}")
            return False

        