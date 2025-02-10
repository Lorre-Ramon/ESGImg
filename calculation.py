from utils import logger, getRunTime
from modules import OpenPDF, DataRetrofitting
from main import getBackUpCopy, getPathBundle
import os 

from typing import List 
import pandas as pd 
import os 

def main(): 
    pass 

@getRunTime("数据补录")
def data_retrofitting_main(batch_size: int, pdf_path_list: List[str]):
    
    distance_df_filepath = os.path.join("output", "distance.xlsx")
    
    if os.path.exists(distance_df_filepath):
        # save a copy for backup
        getBackUpCopy(distance_df_filepath)
        
        df_dist = pd.read_excel(distance_df_filepath)
        # file_mask = df_dist["PDF_name"].unique().tolist()
        # pdf_path_list_masked = [
        #     pdf_path
        #     for pdf_path in pdf_path_list
        #     if os.path.basename(pdf_path).split("-")[2] not in file_mask
        # ]

    # if len(pdf_path_list_masked) < batch_size:
    #     print("Last batch of PDFs")
    # else:
    #     print(f"{len(pdf_path_list_masked)} PDFs left")
    #     pdf_path_list_masked = pdf_path_list_masked[:batch_size]

    for pdf_path in pdf_path_list:
        print(f"Processing {os.path.basename(pdf_path)}")
        try: 
            with OpenPDF(pdf_path, "test_set") as pdf:
                data_retrofitting_task = DataRetrofitting(pdf, df_dist)
                df_dist = data_retrofitting_task.main()
                df_dist.to_excel(distance_df_filepath, index=False)
        except Exception as e:
            logger.error(f"Error processing {os.path.basename(pdf_path)}: {e}")
        
            
def getDataRetrofitting(): 
    pass


if __name__ == "__main__":
    try: 
        logger.info("程序开始")
        print("程序开始")
        pdf_path_list = getPathBundle("data/SUS/2023")
        data_retrofitting_main(10,pdf_path_list)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e
    finally:
        logger.info("程序结束")
        print("程序结束")