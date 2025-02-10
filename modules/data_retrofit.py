from modules import OpenPDF
from utils import logger

import pandas as pd
import os
import math


class DataRetrofitting:
    def __init__(self, pdf_instance: OpenPDF, df_distance: pd.DataFrame):
        self.pdf: OpenPDF = pdf_instance
        self.df_distance: pd.DataFrame = df_distance
        logger.info("Data Retrofitting task init.")

    def main(self):
        """main function of the DataRetrofitting class"""
        self.df_distance.loc[
            (self.df_distance["year"] == self.pdf.year)
            & (self.df_distance["type"] == self.pdf.type)
            & (self.df_distance["thscode"] == self.pdf.thscode),
            "diag",
        ] = self.getDiagonalLength()
        
        self.df_distance.loc[ 
            (self.df_distance["year"] == self.pdf.year)
            & (self.df_distance["type"] == self.pdf.type)
            & (self.df_distance["thscode"] == self.pdf.thscode),         
            "PDF_pages"
        ] = self.pdf.pdf_page_count

    def getDiagonalLength(self) -> float:
        """calculate diagonal length of the PDF page

        Returns:
            float: the length of the
        """
        width, height = self.pdf.pdf[3].rect.width, self.pdf.pdf[2].rect.height

        return math.sqrt(width**2 + height**2)
