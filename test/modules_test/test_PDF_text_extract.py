import unittest
from unittest.mock import patch, MagicMock
import os 
import sys 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules import PDFTextExtract

class TestPDFTextExtract(unittest.TestCase):
    @patch("modules.OpenPDF")
    def test_extractTextListInfo(self, mock_pdf):
        mock_page = MagicMock()
        mock_page.get_text.return_value = [
            (0, 0, 100, 100, "Sample text", None, None)
        ]
        mock_pdf.pdf = [mock_page]
        mock_pdf.pdf_filename = "sample.pdf"

        extractor = PDFTextExtract(mock_pdf)
        result = extractor.extractTextListInfo(0)

        # 断言返回值是否正确
        self.assertEqual(result, [(0, 0, 100, 100, "Sample text", None, None)])
        mock_page.get_text.assert_called_once_with("blocks")

if __name__ == "__main__":
    unittest.main(exit=False)