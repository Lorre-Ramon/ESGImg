import unittest
from unittest.mock import patch

import os 
import sys
import pandas as pd  

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules import DataRetrofitting, OpenPDF

class TestDataRetrofitting(unittest.TestCase):
    def test_main(self): 
        with patch('modules.OpenPDF') as mock_OpenPDF: 
            mock_OpenPDF.return_value.year = 2023
            mock_OpenPDF.return_value.type = "SUS"
            mock_OpenPDF.return_value.thscode = "600073.SH"
            mock_OpenPDF.return_value.pdf_page_count = 73
        df_distance = pd.read_excel("test/data/distance.xlsx")
            
        data_retrofitting_task1 = DataRetrofitting(mock_OpenPDF(), df_distance)
        df_distance2 = data_retrofitting_task1.main()
        print("diagnoal length: ",df_distance2.loc[0, "diag"])
        
        self.assertEqual(df_distance2.columns[-2:].to_list(), ["diag", "PDF_pages"])
        self.assertEqual(df_distance2.loc[0, "PDF_pages"], 73)
        
        
    def mannual_test(self): 
        df_distance = pd.read_excel("test/data/distance.xlsx")
        with OpenPDF("data/SUS/2023/600073.SH-上海梅林-上海梅林：上海梅林2023年度ESG暨可持续发展报告-20240327.pdf", "test_set") as pdf:
            data_retrofitting_task2 = DataRetrofitting(pdf, df_distance)
            
            df_distance2 = data_retrofitting_task2.main()
            
        print("diagnoal length: ",df_distance2.loc[0, "diag"])
        print("pdf_page_count: ",df_distance2.loc[0, "PDF_pages"])
        print(df_distance2.head(5))

if __name__ == '__main__':
    # unittest.main()
    TestDataRetrofitting().mannual_test()