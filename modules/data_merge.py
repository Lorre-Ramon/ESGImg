import pandas as pd
import akshare as ak
import os

from typing import List


class DataMerge:
    def __init__(self, df_distance: pd.DataFrame) -> None:
        self.df_dist = df_distance

    def main(self): 
        
        # clean the data
        if "Unnamed: 0" in self.df_dist.columns:
            self.df_dist.drop(columns=["Unnamed: 0"], axis=1, inplace=True)
        
        self.df_PDF = pd.DataFrame() 
        self.df_PDF[["PDF_name", "thscode"]] = self.df_dist[["PDF_name", "thscode"]].drop_duplicates().reset_index(drop=True)        
        self.df_PDF["Corp_code"] = self.df_PDF["PDF_name"].apply(self.getCorpCode)
        self.df_PDF["Corp_market"] = self.df_PDF["PDF_name"].apply(self.getCorpMkt)
        
        self.df_PDF = self.df_PDF.merge(self.df_dist[['PDF_name', 'thscode', 'year', 'type']], 
                          on=['PDF_name', 'thscode'], 
                          how='left').rename(columns={"type": "Pub_type", "year":"Pub_year"})
        
    def getCorpCode(self, PDF_name:str) -> str:
        """extracts the corporation listed code from the PDF name

        Args:
            PDF_name (str): the value of the column `PDF_name` in the `df_distance` DataFrame

        Returns:
            str: the corporation listed code
        """
        return (
            str(PDF_name.split("-")[0][0:6])
            if PDF_name.split("-")[0][-2:] != "HK"
            else str(PDF_name.split("-")[0][0:5])
        )

    def getCorpMkt(self, PDF_name:str) -> str:
        """extracts the corporation listed market from the PDF name
        
        Args:
            PDF_name (str): the value of the column `PDF_name` in the `df_distance` DataFrame

        Returns:
            str: the corporation listed market
        """
        return (
            PDF_name.split("-")[0][-2:]
        )    
        
    def mergeIndustryCatagories(self) -> None: 
        
        df_StockIndustryCatagories = pd.read_excel("data/BasicInfo/证监会行业分类标准.xlsx")
        if 'Unnamed: 0' in df_StockIndustryCatagories.columns:
            df_StockIndustryCatagories.drop('Unnamed: 0', axis=1, inplace=True)
            
    def readIndustryInfo(self, corp_code:str)  -> str: 
        """reads the industry information from the akshare library and returns the industry code

        Args:
            corp_code (str): the corporation listed code, 6 digits string

        Raises:
            ValueError: if the corporation code is not a 6 digits string
            ValueError: if no industry information is found for the corporation code

        Returns:
            str: the industry code
        """
        df_StockIndustryCatagories = pd.read_excel("data/BasicInfo/证监会行业分类标准.xlsx")
        
        if len(corp_code) != 6: 
            raise ValueError("Corporation code should be a string of length 6") #TODO: maybe update to return None
        industry_name_list = ak.stock_profile_cninfo(symbol = str(corp_code))['所属行业'].values.tolist()
        
        if len(industry_name_list) == 0:
            raise ValueError(f"No industry information found for {corp_code}") #TODO: maybe update to return None
        
        industry_name = industry_name_list[0]
        industry_code = df_StockIndustryCatagories[df_StockIndustryCatagories['类目名称'] == industry_name]['类目编码'].values.tolist()[-1]
        
        return industry_code
    
    def getDummyVariPollutionIndustry(self, corp_industry_code:str) -> bool: 
        
        import json 
        with open("configs/data_merge_configs.json", "r") as f:
            configs = json.load(f) 
            
        self.data_merge_configs = configs["production"]
        
        return corp_industry_code in self.data_merge_configs

    