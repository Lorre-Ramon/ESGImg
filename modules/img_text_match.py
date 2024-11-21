from modules import OpenPDF
from utils import logger 

import jiagu
import string
import numpy as np
import pandas as pd
import torch
import itertools
import re
import os
import pymupdf
import ast
import math

from PIL import Image
from typing import List, Dict, Tuple

import cn_clip.clip as clip
from cn_clip.clip import load_from_name, available_models
# print("Available models:", available_models())


class PDFmatch:
    def __init__(self, pdf_instance: OpenPDF) -> None:
        self.pdf: OpenPDF = pdf_instance

    def calculateCRI(self, df: pd.DataFrame) -> float:
        """calculate the composite reliability index CRI | 计算复合可靠性指数

        How:
            1. Calculate the maximum probability spread (MPS) | 计算最大概率差异度
            1.1 Calculate the delta between the maximum probability and the average of the rest | 计算最大概率与其余部分的平均值的差
            1.2 If the rest is empty, set mps to 0 | 如果其余部分为空，则设置mps为0
            1.3 Else, set mps to the delta | 否则，设置mps为差值

            2. Calculate the standard deviation of probability | 计算概率的标准差

            3. Calculate the composite reliability index | 计算复合可靠性指数
            3.1 Calculate the cri by dividing mps by sd | 通过将mps除以sd来计算cri

        Args:
            df (pd.DataFrame): filtered DataFrame | 过滤后的DataFrame

        Returns:
            float: composite reliability index | 综合可靠性指数
        """
        max_prob = df["prob_sum"].max()
        prob_except_max = df[df["prob_sum"] != max_prob]["prob_sum"]

        # maximum probability spread
        mps = max_prob - prob_except_max.mean() if not prob_except_max.empty else 0

        # standard deviation of probability
        sd = df["prob_sum"].std()

        # composite reliability index
        cri = mps / sd if sd > 0 else 0

        return cri

    def calculateDistance(
        self, img_cord: Tuple[float, float], text_cord: Tuple[float, float]
    ) -> float:
        """calculate the distance between the image and text | 计算图片和文本之间的距离

        Args:
            img_cord (Tuple[float, float])
            text_cord (float, float])

        Returns:
            float: distance between the image and text | 图片和文本之间的距离
        """
        img_x, img_y = img_cord
        text_x, text_y = text_cord
        return math.sqrt((img_x - text_x) ** 2 + (img_y - text_y) ** 2)

    def calculateWordSimiliarity(
        self, labels: List[str], probs, img_path: str, page: int
    ) -> pd.Series:
        """calculate the word similarity between the keywords and image | 计算文本和关键词之间的相似度

        Args:
            labels (List[str]): list of keywords | 关键词列表
            probs (_type_) #TODO: check the type
            img_path (str)
            page (int)

        Returns:
            pd.Series #TODO: check the type
        """
        prob_dict = dict(zip(labels, probs[0]))

        # access the image coordinates | 访问图片坐标
        img_name = os.path.basename(img_path)
        img_cord = self.df_img[self.df_img["file_name"] == img_name][
            "centre_coordinate"
        ]
        [img_cord] = img_cord.values
        img_cord = ast.literal_eval(img_cord)

        # access the text coordinates | 访问文本坐标
        df_min_dis = self.df_text.loc[
            (self.df_text["PDF_name"] == self.pdf.PDF_name)
            & (self.df_text["page"] == page)
        ]
        if not df_min_dis.empty:
            df_min_dis["dis_to_img_current"] = df_min_dis.apply(
                lambda row: self.calculateDistance(
                    img_cord, (row["center_x"], row["center_y"])
                ),
                axis=1,
            )

            return df_min_dis.sort_values(by="dis_to_img_current", ascending=True)[0:1][
                "keyword"
            ].apply(
                lambda keywords: sum(
                    prob_dict.get(k, 0) for k in keywords if pd.notnull(k)
                )
                / (len([k for k in keywords if pd.notnull(k)]) if keywords else 1)
            )
        else: 
            logger.warning(f"pdf: {self.pdf.PDF_name} page: {page} has no text")
            return -1

    def extractKeywordsfromPDF(self) -> pd.DataFrame:
        """extract keywords from the PDF file | 从PDF文件中提取关键词

        Returns:
            pd.DataFrame: DataFrame with keywords from PDF
        """
        pdf_file = self.pdf.pdf
        pdf_name = self.pdf.pdf_filename

        key = []
        for page in range(len(pdf_file)):
            keywords = self.extractKeywordsfromPage(self.pdf.PDF_name, page + 1)
            key.append({"file_name": pdf_name, "page": page + 1, "keywords": keywords})

        df_key = pd.DataFrame(key)
        return df_key

    def extractKeywordsfromPage(self, pdf_name: str, page: int) -> List[str]:
        """extract keywords from a page of the PDF file | 从PDF文件的一页中提取关键词

        Args:
            pdf_name (str): OpenPDF.PDF_name
            page (int): current processing page number

        Returns:
            List[str]: Page keywords list
        """
        keywords_list = []
        keyword = []

        page_rows = self.df_text[self.df_text["PDF_name"] == pdf_name]["page"].unique()

        for idx, row in page_rows.iterrows():
            if pd.notna(
                row["content"]
            ):  # FIXME: old version: if not pd.isna(row["content"]):
                keywords = self.extractKeywordsfromText(row["content"])

            self.df_text["keyword"] = self.df_text["keyword"].astype("object")
            self.df_text.at[idx, "keyword"] = keywords

            keywords_list.append(keywords)
            keyword = list(itertools.chain.from_iterable(keywords_list))

        return keyword

    def extractKeywordsfromText(self, text: str, key_num: int = None) -> List[str]:
        """extract keywords from text | 从文本中提取关键词

        Args:
            text (str)
            key_num (int, optional): 提取的关键词数量. Defaults to None.

        Returns:
            List[str]: 关键词列表
        """
        if key_num is None:
            key_num = len(text) // 20 + 2  # TODO: should be put in config

        text_cleaned = self.removeSymbol(text)
        keywords = jiagu.keywords(text_cleaned, key_num)
        return keywords

    def readData(self, text_filepath: str, img_filepath: str) -> None:
        """read the DataFrame with text and image information | 读入包含文本和图片信息的DataFrame

        Args:
            text_filepath (str): 文本文件路径
            img_filepath (str): 图片文件路径
        """
        df_text = pd.read_excel(text_filepath)
        df_img = pd.read_excel(img_filepath)
        df_img = df_img.drop_duplicates(subset="file_name")

        self.df_text = df_text
        self.df_img = df_img

    def removeSymbol(self, text: str) -> str:
        """remove the punctuation and spaces in text | 去除文本中的符号标点和空格

        Args:
            text (str)

        Returns:
            str
        """
        text = text.translate(
            str.maketrans("", "", string.punctuation)
        )  # remove all punctuation
        text = re.sub(r"\s+", "", text)  # remove all white spaces

        return text
