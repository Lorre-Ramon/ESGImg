from modules import OpenPDF, PDFImgExtract
from utils import logger, getRunTime

import os 
import pandas as pd 

def main(pdf_path:str) -> None: 
    os.makedirs("output", exist_ok=True)
    
    with OpenPDF(pdf_path, "test_set") as pdf: 
        # extract_images(pdf)
        extract_text(pdf)

@getRunTime("提取PDF文件图片")
def extract_images(pdf:OpenPDF) -> None: 
    """提取PDF文件中的图片

    Args:
        pdf (PDF_data): PDF_data数据类,正在读取的PDF文件   

    Raises:
        e: Anomaly exception for debugging
    """
    img_coords_df_filepath = os.path.join("output", "img_coords.xlsx")
    if os.path.exists(img_coords_df_filepath): 
        img_coords_df = pd.read_excel(img_coords_df_filepath)
    else:
        img_coords_df = pd.DataFrame(columns=["file_name", "x0", "y0", "x1", "y1", 
                                          "centre_coordinate"])
    
    try:
        pdf_img_extract = pdf.getPDFImgExtract()
        logger.info(f"pdf: {pdf.pdf_filename}开始提取图片")
        img_coords_df_temp:pd.DataFrame = pdf_img_extract.main()
        img_coords_df = pd.concat([img_coords_df, img_coords_df_temp], ignore_index=True)
        img_coords_df.to_excel(img_coords_df_filepath, index=False)
    except Exception as e: 
        logger.error(f"Error: pdf: {pdf.pdf_filename}\n\t{e}")
        raise e
    finally: 
        logger.info(f"pdf: {pdf.pdf_filename}完成提取图片")
        
@getRunTime("提取PDF文件文本")
def extract_text(pdf:OpenPDF) -> None: 
    
    text_coords_df_filepath = os.path.join("output", "text_coords.xlsx")
    if os.path.exists(text_coords_df_filepath): 
        text_coords_df = pd.read_excel(text_coords_df_filepath)
    else:
        text_coords_df = pd.DataFrame(columns=["PDF_name", "page", "p_index", 
                                    "content", "center_x", "center_y"])

    try: 
        pdf_text_extract = pdf.getPDFTextExtract()
        logger.info(f"pdf: {pdf.pdf_filename}开始提取文本")
        text_coords_df_temp = pdf_text_extract.main()
        text_coords_df = pd.concat([text_coords_df, text_coords_df_temp], ignore_index=True)
        text_coords_df.to_excel(text_coords_df_filepath, index=False) 
    except Exception as e: 
        logger.error(f"Error: pdf: {pdf.pdf_filename}\n\t{e}")
        raise e
    finally: 
        logger.info(f"pdf: {pdf.pdf_filename}完成提取文本")
        
        
if __name__ == "__main__": 
    pdf_path = "data/SUS/2022/00941.HK-中国移动-中国移动 2022年度可持续发展报告-2023-03-24.pdf"
    
    try:
        logger.info("程序开始")
        print("程序开始")
        main(pdf_path)
    except Exception as e: 
        logger.error(f"Error: {e}")
        raise e
    finally:
        logger.info("程序结束")
        print("程序结束")
