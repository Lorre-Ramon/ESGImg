import unittest
from unittest.mock import patch

import os 
import sys
import pandas as pd  

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules import DataRetrofitting

class TestDataRetrofitting(unittest.TestCase):
    def test_main(self): 
        with patch('modules.OpenPDF') as mock_OpenPDF: 
            mock_OpenPDF.return_value.year = 2023
            mock_OpenPDF.return_value.type = "SUS"
            mock_OpenPDF.return_value.thscode = "600073.SH"
            mock_OpenPDF.return_value.pdf_page_count = 100
        df_distance = pd.read_excel("test/data/distance.xlsx")
            
        data_retrofitting_task1 = DataRetrofitting(mock_OpenPDF(), df_distance)
        df_distance2 = data_retrofitting_task1.main()
        
        self.assertEqual(df_distance2.columns[-2:], ["diag", "PDF_pages"])
        
if __name__ == '__main__':
    unittest.main()