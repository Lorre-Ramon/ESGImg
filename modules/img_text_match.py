from modules import OpenPDF
from utils import logger

import jiagu
import json
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
from typing import List, Dict, Tuple, Optional, Any

import cn_clip.clip as clip
from cn_clip.clip import load_from_name, available_models
# print("Available models:", available_models())


class PDFMatch:
    def __init__(self, pdf_instance: OpenPDF, global_config_name: str) -> None:
        self.pdf: OpenPDF = pdf_instance
        self.global_config_name = global_config_name

        with open("configs/global_configs.json", "r") as f:
            global_configs = json.load(f)
        self.global_config = global_configs[self.global_config_name]

    def main(self) -> pd.DataFrame:
        """main function to match the text and image | 匹配文本和图片的主函数

        Raises:
            ValueError: raise error if no object text | 如果没有对象文本，则引发错误

        Returns:
            pd.DataFrame: DataFrame for image and matched text | 图像和匹配文本的DataFrame
        """
        
        self.readData(self.pdf.text_coords_df_filepath, self.pdf.img_coords_df_filepath)
        
        df_key = self.extractKeywordsfromPDF()
        for row in self.df_img.loc[
            self.df_img["PDF_name"] == self.pdf.PDF_name
        ].itertuples():
            img_name = row.file_name
            page = row.page
            p_index = row.p_index
            img_cord = row.centre_coordinate

            # read in image | 读入图片
            img_path = os.path.join(str(self.pdf.img_folder_path), str(img_name))
            # read in keywords | 读入关键词
            [keywords] = list(
                df_key.loc[
                    (df_key["file_name"] == self.pdf.pdf_filename)
                    & (df_key["page"] == page)
                ]["keywords"]
            )
            
            # calculate the probability of the image and keywords | 计算图片和关键词的概率
            probs= self.calculateImgKeywordProbability(img_path, keywords)
            
            ws = self.calculateWordSimiliarity(keywords, probs, img_path, page)
            if isinstance(ws, pd.Series): 
                [ws] = list(ws) 
            self.df_img.loc[self.df_img["file_name"] == img_name, "word_simi"] = ws
                
            # match the text and image | 匹配文本和图片
            object_text = self.matchTextImg(keywords, probs, img_path, page)
            print(object_text)
            if object_text is not None:
                # get the text coordinates | 获取文本坐标
                text_cord_list = self.df_text.loc[
                    (self.df_text["PDF_name"] == self.pdf.PDF_name)
                    & (self.df_text["page"] == page)
                    & (self.df_text["content"] == object_text)
                ][['center_x', 'center_y']].values.tolist()
                
                if text_cord_list: 
                    text_cord = text_cord_list[0]
                else: 
                    [text_cord] = text_cord_list
                
                # calculate the distance between the image and text | 计算图片和文本之间的距离
                if isinstance(img_cord, str): 
                    img_cord:tuple = ast.literal_eval(img_cord) 
                    
                dist = self.calculateDistance(img_cord, text_cord) 
                self.df_img.loc[self.df_img["file_name"] == img_name, "distance"] = dist
            else: 
                logger.info(f"pdf: {self.pdf.PDF_name} page: {page} has no object text")
                # raise ValueError(f"pdf: {self.pdf.PDF_name} page: {page} has no object text") 
                
        return self.df_img

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

    def calculateImgKeywordProbability(
        self, img_path: str, keywords: List[str]
    ) -> List:
        """calculate the probability of the image and keywords in a page | 计算图片和当页关键词的概率

        Args:
            img_path (str): image path | 图片路径
            keywords (List[str]): list of keywords of the image's page | 图片所在页的关键词列表

        Raises:
            NotImplementedError: unrealized cuda option | 未实现的cuda选项

        Returns:
            List: list of probabilities for keywords | 关键词的概率列表
        """
        model, preprocess = load_from_name("RN50", device="cpu", download_root="./")
        model.eval()

        device = self.global_config["device"]
        if (device == "mps") and (torch.backends.mps.is_available()):
            device = "mps"
        else:
            device = "cpu"
        if device == "cuda":
            raise NotImplementedError(
                "Cuda option not implemented"
            )  # TODO: enable cuda

        model = model.to(device)
        image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
        label = clip.tokenize(keywords).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image)
            text_features = model.encode_text(label)
            # 对特征进行归一化 | Normalize the features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)

            logits_per_image, logits_per_text = model.get_similarity(image, label)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()

        return probs

    def calculateWordSimiliarity(
        self, labels: List[str], probs, img_path: str, page: int
    ) -> pd.Series | int:
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
            keywords = self.extractKeywordsfromPage(pdf_name, page + 1)
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

        # page_rows:pd.DataFrame = self.df_text[self.df_text["PDF_name"] == pdf_name]["page"].unique() #XXX: Potential mistake version
        page_rows = self.df_text[
            (self.df_text["PDF_name"] == pdf_name) & (self.df_text["page"] == page)
        ]

        for idx, row in page_rows.iterrows():
            if pd.notna(
                row["content"]
            ):  
                keywords = self.extractKeywordsfromText(row["content"])

            self.df_text["keyword"] = None 
            self.df_text["keyword"] = self.df_text["keyword"].astype("object")
            self.df_text.at[idx, "keyword"] = keywords

            keywords_list.append(keywords)
            keyword = list(itertools.chain.from_iterable(keywords_list))

        return keyword

    def extractKeywordsfromText(
        self, text: str, key_num: Optional[int] = None
    ) -> List[str]:
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

    def matchTextImg(
        self, keywords: List[str], probs, img_path: str, page: int
    ) -> Optional[str]: #FIX: unable to yield correct output
        """match the text and image | 匹配文本和图片

        Args:
            keywords (List[str]): list of keywords | 关键词列表
            probs (_type_): list of probabilities for keywords | 关键词的概率列表
            img_path (str): image path | 图片路径
            page (int): current processing page number (for this image) | 当前处理的页码（对于此图片）

        Returns:
            Optional[str]: matched text for given image | 给定图片的匹配文本
        """
        prob_dict = dict(zip(keywords, probs[0]))
        filtered_df = self.df_text.loc[
            (self.df_text["PDF_name"] == self.pdf.pdf_filename)
            & (self.df_text["page"] == page)
        ]
        if not filtered_df.empty:
            filtered_df = filtered_df[pd.notnull(filtered_df["keyword"])]

            # create a new column to store the probability sum of the keywords | 创建一个新列来存储关键词的概率和
            filtered_df["prob_sum"] = filtered_df["keyword"].apply(
                lambda keywords: sum(
                    prob_dict.get(k, 0) for k in keywords if pd.notnull(k)
                )
                / (len([k for k in keywords if pd.notnull(k)]) if keywords else 1)
            )

            # iterate through the column | 遍历列
            filtered_df["prob_sum"] = filtered_df["prob_sum"].apply(
                lambda x: 0.0 if not isinstance(x, float) else x
            )

            if not filtered_df["prob_sum"].empty:
                max_prob_content = filtered_df.loc[
                    filtered_df["prob_sum"].idxmax(), "content"
                ]
                max_prob = filtered_df["prob_sum"].max()
                cri = self.calculateCRI(filtered_df)
            else:  # if prob_sum is empty | 如果 prob_sum 列为空
                max_prob_content = None
                max_prob = None
                cri = None

            # record the matched text | 记录匹配的文本
            img_name = os.path.basename(img_path)
            self.df_img.loc[self.df_img["file_name"] == img_name, "match_text"] = (
                max_prob_content
            )
            self.df_img.loc[self.df_img["file_name"] == img_name, "match_text_prob"] = (
                max_prob
            )
            self.df_img.loc[self.df_img["file_name"] == img_name, "match_text_CRI"] = (
                cri
            )

            return max_prob_content

    def readData(
        self, text_coords_df_filepath: str|None, img_coords_df_filepath: str|None
    ) -> None:
        """read the DataFrame with text and image information | 读入包含文本和图片信息的DataFrame

        Args:
            text_coords_df_filepath (str|None): 文本文件路径
            img_coords_df_filepath (str|None): 图片文件路径
        """
        if isinstance(text_coords_df_filepath, str) and isinstance(img_coords_df_filepath, str):
            df_text = pd.read_excel(text_coords_df_filepath)
            df_img = pd.read_excel(img_coords_df_filepath)
            df_img = df_img.drop_duplicates(subset="file_name")

            self.df_text = df_text
            self.df_img = df_img
        else:
            raise ValueError("text_coords_df_filepath and img_coords_df_filepath are both not str")

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
