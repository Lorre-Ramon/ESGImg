

import pandas as pd 
import akshare as ak
import os 
import fitz
import math

class DataRetrofit:
    def __init__(self, filepath, PDF_folder, PDF_year, PDF_type):
        self.filepath = filepath
        self.PDF_folder = PDF_folder
        self.PDF_year = PDF_year
        self.PDF_type = PDF_type

    def pages(self, PDF_path):
        pdf_file = fitz.open(PDF_path)
        return pdf_file.page_count

    def diagonal(self, PDF_path):
        pdf_file = fitz.open(PDF_path)
        width, height = pdf_file[3].rect.width, pdf_file[2].rect.height
        return math.sqrt(width**2 + height**2)

    def corp_code(self, PDF_name):
        return str(PDF_name.split("-")[0][0:6]) if PDF_name.split("-")[0][-2:] != 'HK' else str(PDF_name.split("-")[0][0:5])

    def corp_market(self, PDF_name):
        return PDF_name.split("-")[0][-2:]

    def get_df_PDF(self):
        df_img = pd.read_excel(self.filepath)
        if "Unnamed: 0" in df_img.columns:
            df_img = df_img.drop("Unnamed: 0", axis=1)

        values_to_remove = [
            "华为2022.pdf", "万科2022.pdf",
            "601966.SH-玲珑轮胎-玲珑轮胎 山东玲珑轮胎股份有限公司2022年可持续发展报告英文版-2023-04-29.pdf",
            "002129.SZ-TCL中环-TCL中环 TCL中环新能源科技股份有限公司2022年度可持续发展报告(英文版)-2023-03-29.pdf",
            "000726.SZ-鲁泰A-鲁泰Ａ 鲁泰纺织可持续发展报告2022-英文版-2023-04-12.pdf"
        ]
        df_img = df_img[~df_img['PDF_name'].isin(values_to_remove)]

        df_PDF = pd.DataFrame()
        df_PDF['PDF_name'] = df_img['PDF_name'].unique()
        df_PDF['Corp_code'] = df_PDF['PDF_name'].apply(self.corp_code)
        df_PDF['Corp_market'] = df_PDF['PDF_name'].apply(self.corp_market)
        df_PDF['Pub_year'] = self.PDF_year
        df_PDF['Pub_type'] = self.PDF_type

        df_PDF['PDF_pages'] = df_PDF['PDF_name'].apply(lambda x: self.pages(os.path.join(self.PDF_folder, x)))

        df_PDF = df_PDF.merge(df_img.groupby('PDF_name')['page'].count().reset_index(name='img_num'),
                              on='PDF_name', how='left')

        df_img['img_size'] = df_img.apply(lambda row: abs(row["x1"] - row["x0"]) * abs(row["y1"] - row["y0"]), axis=1)
        df_PDF = df_PDF.merge(df_img.groupby('PDF_name')['img_size'].mean().reset_index(name='img_size_avg'),
                              how='left', on='PDF_name')

        df_PDF['img_num_pages_ratio'] = df_PDF.apply(lambda row: row['img_num'] / row['PDF_pages'], axis=1)
        df_PDF['img_size_pages_ratio'] = df_PDF.apply(lambda row: row['img_size_avg'] / row['PDF_pages'], axis=1)

        diagonal_series = df_PDF['PDF_name'].apply(lambda x: self.diagonal(os.path.join(self.PDF_folder, x)))
        diagonal_series.index = df_PDF['PDF_name']

        diagonal_compute = pd.merge(diagonal_series.reset_index(name='diag'),
                                    df_img.groupby('PDF_name')['distance'].mean().reset_index(name='dist_avg'),
                                    on='PDF_name', how='left')
        diagonal_compute['dist_diag_ratio'] = diagonal_compute.apply(lambda row: row['dist_avg'] / row['diag'], axis=1)
        df_PDF = pd.merge(df_PDF, diagonal_compute[['PDF_name', 'dist_diag_ratio']], on='PDF_name', how='left')

        df_PDF = pd.merge(df_PDF, df_img.groupby("PDF_name")['word_simi'].mean().reset_index(name='word_simi_avg'),
                          on='PDF_name', how='left')

        output_path = f"/Users/improvise/Desktop/保研/实证论文/ESG/Playground/05_DataIntegration2/00_separate/df_PDF_{self.PDF_type}_{self.PDF_year}.xlsx"
        df_PDF.to_excel(output_path)

        return df_PDF