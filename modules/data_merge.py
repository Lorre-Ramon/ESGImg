import pandas as pd
import os


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

    
