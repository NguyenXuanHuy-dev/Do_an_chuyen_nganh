import os
import pandas as pd
from typing import Dict, List, Tuple
from docx import Document
from werkzeug.utils import secure_filename
from config import Config
from services.preprocess_service import PreprocessService

class FileService:
    @staticmethod
    def allowed_file(filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @classmethod
    def save_upload_file(cls, file) -> Tuple[str, str, str]:
        """
        Saves uploaded file securely and returns (filepath, original_filename, extension).
        """
        original_name = file.filename
        ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else ''
        filename = secure_filename(original_name)
        if not filename:
            filename = f"upload_{ext}"
            
        save_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(save_path)
        return save_path, original_name, ext

    @classmethod
    def extract_texts_from_file(cls, file_path: str, ext: str) -> Tuple[List[str], List[str]]:
        """
        Extracts raw feedback lines and possible column headers from file.
        Returns: (raw_texts, column_names)
        """
        raw_texts: List[str] = []
        columns: List[str] = []

        if ext in ['xlsx', 'xls']:
            try:
                df = pd.read_excel(file_path)
                columns = [str(c) for c in df.columns]
                # Find most relevant text column
                target_col = cls._find_best_text_column(df)
                if target_col is not None:
                    raw_texts = df[target_col].dropna().astype(str).tolist()
                else:
                    # Fallback to first string column
                    for col in df.columns:
                        vals = df[col].dropna().astype(str).tolist()
                        if vals and len(vals) > 0:
                            raw_texts = vals
                            break
            except Exception as e:
                print(f"Error reading excel: {e}")

        elif ext == 'csv':
            encodings = ['utf-8', 'utf-8-sig', 'cp1258', 'latin-1']
            for enc in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    columns = [str(c) for c in df.columns]
                    target_col = cls._find_best_text_column(df)
                    if target_col is not None:
                        raw_texts = df[target_col].dropna().astype(str).tolist()
                    else:
                        raw_texts = df.iloc[:, 0].dropna().astype(str).tolist()
                    break
                except Exception:
                    continue

        elif ext == 'docx':
            try:
                doc = Document(file_path)
                for p in doc.paragraphs:
                    t = p.text.strip()
                    if t:
                        raw_texts.append(t)
                for table in doc.tables:
                    for row in table.rows:
                        row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_texts:
                            raw_texts.append(" - ".join(row_texts))
            except Exception as e:
                print(f"Error reading docx: {e}")

        elif ext == 'txt':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str:
                            raw_texts.append(line_str)
            except Exception as e:
                print(f"Error reading txt: {e}")

        return raw_texts, columns

    @classmethod
    def _find_best_text_column(cls, df: pd.DataFrame):
        keywords = ['bình luận', 'đánh giá', 'nhận xét', 'nội dung', 'comment', 'review', 'feedback', 'text', 'content', 'ý kiến', 'phản hồi']
        for col in df.columns:
            col_lower = str(col).lower()
            if any(k in col_lower for k in keywords):
                return col
                
        # If no column name matches, choose the column with highest average string length
        best_col = None
        max_avg_len = 0
        for col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                avg_len = non_null.astype(str).map(len).mean()
                if avg_len > max_avg_len:
                    max_avg_len = avg_len
                    best_col = col

        return best_col

    @classmethod
    def preview_and_diagnose(cls, raw_texts: List[str]) -> Dict:
        """
        Diagnoses file data: finds empty lines, duplicates, junk strings,
        and generates a clean preview for user confirmation.
        """
        diagnosis = PreprocessService.detect_noise_and_errors(raw_texts)
        
        # Take first 10 preview items
        preview_samples = diagnosis['valid_items'][:10]
        
        return {
            'total_raw_rows': diagnosis['total_raw'],
            'empty_rows': diagnosis['empty_count'],
            'duplicate_rows': diagnosis['duplicate_count'],
            'clean_rows': diagnosis['clean_count'],
            'preview_samples': preview_samples,
            'noise_rate_pct': round(((diagnosis['empty_count'] + diagnosis['duplicate_count']) / max(1, diagnosis['total_raw'])) * 100, 1)
        }
