from modules import * 
from utils import *

if __name__ == "__main__": 
    pdf_path = "data/00_SustainabilityReport_PDF/2022/00941.HK-中国移动-中国移动 2022年度可持续发展报告-2023-03-24.pdf"
    
    try:
        pdf = PDFExtract(pdf_path)
        pdf.pdf_info
    except Exception as e: 
        logger.error(f"Error: {e}")
        raise e
