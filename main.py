from modules import OpenPDF
from utils import logger, getRunTime

import os
import pandas as pd
from typing import List



def main(batch_size: int, pdf_path_list: List[str]) -> None:
    os.makedirs("output", exist_ok=True)
    # pdf_name_list = [os.path.basename(pdf_path).split("-")[2] for pdf_path in pdf_path_list]

    # remove PDFs that have been processed
    pdf_path_list_masked = pdf_path_list[:batch_size]
    if os.path.exists("output/distance.xlsx"):
        # save a copy for backup
        getBackUpCopy("output/distance.xlsx")
        getBackUpCopy("output/img_coords.xlsx")
        getBackUpCopy("output/text_coords.xlsx")

        df_dist = pd.read_excel("output/distance.xlsx")
        file_mask = df_dist["PDF_name"].unique().tolist()
        pdf_path_list_masked = [
            pdf_path
            for pdf_path in pdf_path_list
            if os.path.basename(pdf_path).split("-")[2] not in file_mask
        ]

    if len(pdf_path_list_masked) < batch_size:
        print("Last batch of PDFs")
    else:
        print(f"{len(pdf_path_list_masked)} PDFs left")
        pdf_path_list_masked = pdf_path_list_masked[:batch_size]

    for pdf_path in pdf_path_list_masked:
        print(f"Processing {os.path.basename(pdf_path)}")
        try:
            with OpenPDF(pdf_path, "test_set") as pdf:
                match pdf:
                    case _ if pdf.mkt == "HK":
                        logger.info(f"pdf: {pdf.pdf_filename}为港股PDF，跳过")
                        print(f"{pdf.pdf_filename} is a HK PDF, skip")
                        os.rename(
                            pdf_path,
                            os.path.join(
                                os.path.dirname(pdf_path),
                                "error file",
                                os.path.basename(pdf_path),
                            ),
                        )
                    case _ if "英文" in pdf.PDF_name:
                        logger.info(f"pdf: {pdf.pdf_filename}为英文PDF，跳过")
                        print(f"{pdf.pdf_filename} is an English PDF, skip")
                        os.rename(
                            pdf_path,
                            os.path.join(
                                os.path.dirname(pdf_path),
                                "error file",
                                os.path.basename(pdf_path),
                            ),
                        )
                    case _:
                        extract_images(pdf)
                        extract_text(pdf)
                        match_img_text(pdf)

        except Exception as e:
            logger.error(
                f"\nBad PDF file, pdf: {os.path.basename(pdf_path).split('-')[2]} has Error: {e}"
            )
            print(f"\nBad PDF file, Error: {e}")
            os.rename(
                pdf_path,
                os.path.join(
                    os.path.dirname(pdf_path), "error file", os.path.basename(pdf_path)
                ),
            )
            continue


@getRunTime("提取PDF文件图片")
def extract_images(pdf: OpenPDF) -> None:
    """Extract images from PDF file | 提取PDF文件中的图片

    Args:
        pdf (OpenPDF): OpenPDF,the ongoing PDF file

    Raises:
        e: Anomaly exception for debugging
    """
    img_coords_df_filepath = os.path.join("output", "img_coords.xlsx")
    pdf.img_coords_df_filepath = img_coords_df_filepath
    if os.path.exists(img_coords_df_filepath):
        img_coords_df = pd.read_excel(img_coords_df_filepath)
    else:
        img_coords_df = pd.DataFrame(
            columns=["file_name", "x0", "y0", "x1", "y1", "centre_coordinate"]
        )

    try:
        pdf_img_extract = pdf.getPDFImgExtract()
        logger.info(f"pdf: {pdf.pdf_filename}开始提取图片")
        img_coords_df_temp: pd.DataFrame = pdf_img_extract.main()
        img_coords_df = pd.concat(
            [img_coords_df, img_coords_df_temp], ignore_index=True
        )
        img_coords_df.to_excel(img_coords_df_filepath, index=False)
        # img_coords_df.to_excel(os.path.join("output", "backup", os.path.basename(img_coords_df_filepath)), index=False)
    except Exception as e:
        logger.error(f"Error: pdf: {pdf.pdf_filename}\n\t{e}")
        raise e
    finally:
        logger.info(f"pdf: {pdf.pdf_filename}完成提取图片")


@getRunTime("提取PDF文件文本")
def extract_text(pdf: OpenPDF) -> None:
    """Extract text from PDF file | 提取PDF文件中的文本

    Args:
        pdf (OpenPDF): 正在读取的PDF文件

    Raises:
        e: Anomaly exception for debugging
    """
    text_coords_df_filepath = os.path.join("output", "text_coords.xlsx")
    pdf.text_coords_df_filepath = text_coords_df_filepath
    if os.path.exists(text_coords_df_filepath):
        text_coords_df = pd.read_excel(text_coords_df_filepath)
    else:
        text_coords_df = pd.DataFrame(
            columns=["PDF_name", "page", "p_index", "content", "center_x", "center_y"]
        )

    try:
        pdf_text_extract = pdf.getPDFTextExtract()
        logger.info(f"pdf: {pdf.pdf_filename}开始提取文本")
        text_coords_df_temp = pdf_text_extract.main()
        text_coords_df = pd.concat(
            [text_coords_df, text_coords_df_temp], ignore_index=True
        )
        text_coords_df.to_excel(text_coords_df_filepath, index=False)
        # text_coords_df.to_excel(os.path.join("output", "backup", os.path.basename(text_coords_df_filepath)), index=False)
    except Exception as e:
        logger.error(f"Error: pdf: {pdf.pdf_filename}\n\t{e}")
    finally:
        logger.info(f"pdf: {pdf.pdf_filename}完成提取文本")


def getPathBundle(path: str) -> List[str]:
    """获取路径下所有PDF文件

    Args:
        path (str): 文件夹路径

    Returns:
        List[str]: PDF文件路径列表
    """
    files = [f for f in os.listdir(path) if f.endswith(".pdf")]
    return [os.path.join(path, f) for f in files]

def getBackUpCopy(source_filepath: str) -> None:
    """Create a backup copy of the source file | 创建源文件备份

    Args:
        source_filepath (str): The path of the source file | 源文件路径
    """
    from datetime import datetime
    import shutil

    timestamp = datetime.now().strftime("%Y%m%d_%H")
    try:
        os.makedirs("output/backup", exist_ok=True)
        shutil.copy(
            source_filepath,
            f"output/backup/{os.path.basename(source_filepath)}_{timestamp}.xlsx",
        )
        logger.info(
            f"{os.path.basename(source_filepath)}，已备份为output/backup/{os.path.basename(source_filepath)}_{timestamp}.xlsx"
        )
        print(
            f"{os.path.basename(source_filepath)}，已备份为output/backup/{os.path.basename(source_filepath)}_{timestamp}.xlsx"
        )
    except Exception as e:
        logger.error(f"Error: {e}")

@getRunTime("匹配PDF文件图文")
def match_img_text(pdf: OpenPDF) -> None:
    """Match images and text in PDF file | 匹配PDF文件中的图片和文本

    Args:
        pdf (OpenPDF): 正在读取的PDF文件

    Raises:
        e: Anomaly exception for debugging | 异常以进行调试
    """
    distance_df_filepath = os.path.join("output", "distance.xlsx")
    pdf.distance_df_filepath = distance_df_filepath
    if os.path.exists(distance_df_filepath):
        distance_df = pd.read_excel(distance_df_filepath)
    else:
        distance_df = pd.DataFrame(
            columns=[
                "file_name",
                "x0",
                "y0",
                "x1",
                "y1",
                "centre_coordinate",
                "PDF_name",
                "page",
                "p_index",
                "word_simi",
                "match_text",
                "match_text_prob",
                "match_text_CRI",
                "distance",
            ]
        )

    try:
        pdf_match_img_text = pdf.getPDFmatch("test_set")
        logger.info(f"pdf: {pdf.pdf_filename}开始匹配图片和文本")
        distance_df_temp = pdf_match_img_text.main()
        distance_df = pd.concat([distance_df, distance_df_temp], ignore_index=True)
        distance_df.to_excel(distance_df_filepath, index=False)
        # distance_df.to_excel(os.path.join("output", "backup", os.path.basename(distance_df_filepath)), index=False)
    except Exception as e:
        logger.error(f"Error: pdf: {pdf.pdf_filename}\n\t{e}")
        raise e
    finally:
        logger.info(f"pdf: {pdf.pdf_filename}完成匹配图片和文本")


if __name__ == "__main__":
    """test_path
    pdf_path = (
         "data/SUS/2022/00941.HK-中国移动-中国移动 2022年度可持续发展报告-2023-03-24.pdf"
    ) 
    """

    try:
        logger.info("程序开始")
        print("程序开始")
        pdf_path_list = getPathBundle("data/ESG/2023")
        # pdf_path_list = getPathBundle('data/SUS/2022')
        # pdf_path_list = getPathBundle('data/SUS/2023/error file')
        main(100, pdf_path_list)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e
    finally:
        logger.info("程序结束")
        print("程序结束")
