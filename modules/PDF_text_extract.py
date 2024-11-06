from utils import logger
from modules import OpenPDF

import pandas as pd 
from typing import Tuple, List, Any

import warnings 
warnings.filterwarnings("ignore")
    
class PDFTextExtract: 
    def __init__(self, pdf_instance: OpenPDF) -> None:
        """初始化PDFTextExtract类

        Args:
            pdf_instance (OpenPDF): 打开的PDF实例
        """
        self.pdf = pdf_instance 
            
        self.textblock_y_threshold = self.pdf.global_config['textblock_y_threshold']
        self.header_footer_threshold = self.pdf.global_config['header_footer_threshold']
        
    def main(self) -> pd.DataFrame: 
        """主函数
        
        Returns:
            pd.DataFrame: 提取的PDF文本信息
        """
        paragraphs:List[str] = []
        coordinates:List[Tuple[float, float]] = []
        text_df:pd.DataFrame = pd.DataFrame(columns=["PDF_name", "page", "p_index", "content", "center_x", "center_y"])
               
        for page_num in range(self.pdf.pdf_page_count):
            blocks = self.extractTextListInfo(page_num) 
            if blocks == []:
                continue
            
            page_height = self.pdf.pdf[page_num].rect.height
            
            init_text = ""
            x0_init, y0_init, x1_init, y1_init = blocks[0][:4]
            
            for block in blocks: 
                if self.extractTextInfo(block) is None: 
                    continue
                else:
                    x0, y0, x1, y1, text = self.extractTextInfo(block)
                     
                y_close_enough = abs(y0 - y0_init) < self.textblock_y_threshold 
                if y_close_enough: 
                    init_text += text.strip()
                    x1_init = max(x1, x1_init)
                    y1_init = max(y1, y1_init)
                else: 
                    paragraphs.append(init_text.replace(" ", ""))
                    coordinates.append(((x0_init + x1_init) / 2, (y0_init + y1_init) / 2))
                    
                    init_text = text.strip()
                    x0_init, y0_init, x1_init, y1_init = x0, y0, x1, y1
            
            # save the last paragraph
            paragraphs.append(init_text.replace(" ", ""))
            coordinates.append(((x0_init + x1_init) / 2, (y0_init + y1_init) / 2))
            
            # save the extracted text to a dataframe
            index = 0
            for para, coord in zip(paragraphs, coordinates): 
                center_x, center_y = coord
                if not self.isHeaderOrFooter(center_y, page_height): 
                    info = pd.Series(["", page_num+1, index, para, center_x, center_y], 
                                    index=["PDF_name", "page", "p_index", 
                                            "content", "center_x", "center_y"])
                    text_df = pd.concat([text_df, pd.DataFrame([info])], ignore_index=True)
                
                index += 1
        
        return text_df
    
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
        
    def extractTextInfo(self, block:List) -> List[Tuple[float,float,float,float,str]]: 
        """提取PDF单个文本段的信息

        Args:
            block (List)

        Returns:
            List[float,float,float,float,str]: 具体地址信息和文本内容
                List[0]: block_x0: 文本段左上角x坐标
                List[1]: block_y0: 文本段左上角y坐标
                List[2]: block_x1: 文本段右下角x坐标
                List[3]: block_y1: 文本段右下角y坐标
                List[4]: block_text: 文本段内容
        """
        match block: 
            case _ if "<image:" in block[4]: 
                logger.info(f"pdf: {self.pdf.pdf_filename} page: {block[0]} text: {block[4]}为图像信息块，忽略")
                return None
            case _: 
                x0, y0, x1, y1, text = block[0:5]
                return x0, y0, x1, y1, text
            
    def isHeaderOrFooter(self, center_y:float, page_height:float) -> bool: 
        """判断文本段是否为页眉或页脚

        Args:
            center_y (float): 文本段中心y坐标
            page_height (float): PDF页高

        Returns:
            bool: 是否为页眉或页脚
        """
        match center_y: 
            case _ if center_y < self.header_footer_threshold: 
                return True 
            case _ if center_y > (page_height - self.header_footer_threshold):
                return True
            case _: 
                return False