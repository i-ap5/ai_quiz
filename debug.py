# generate_raw_text.py
import pdfplumber
import docx
import json
import os
import re

# --- CONFIGURATION ---
# IMPORTANT: Change this to the exact filename of the PDF or DOCX you want to analyze.
FILE_TO_ANALYZE = "tt.pdf" 
JSON_OUTPUT_FILE = "raw_text_output2.json"

def extract_and_save_raw_text(file_path):
    """
    Reads a PDF or DOCX file, extracts the raw text content, and saves it to a JSON file
    for analysis. This shows us exactly what the AI will be working with.
    """
    if not os.path.exists(file_path):
        print(f"--- ERROR ---")
        print(f"File not found: '{file_path}'")
        print("Please make sure the file is in the same folder and the filename is correct.")
        return

    print(f"Reading raw text from '{file_path}'...")
    full_text = ""
    file_type = os.path.splitext(file_path)[1].lower()

    try:
        if file_type == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        
        elif file_type == ".docx":
            doc = docx.Document(file_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
        
        else:
            print(f"--- ERROR: Unsupported file type '{file_type}' ---")
            return

        # Prepare the data for JSON output
        output_data = {
            "source_file": file_path,
            "extracted_text": full_text
        }
        
        # Save the extracted text to a JSON file
        with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n--- SUCCESS ---")
        print(f"Raw text has been extracted and saved to '{JSON_OUTPUT_FILE}'.")
        print("Please open that file to see what the script is reading from your document.")

    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"An unexpected error occurred: {e}")
        print("The file might be corrupted or in an unsupported format.")


if __name__ == "__main__":
    extract_and_save_raw_text(FILE_TO_ANALYZE)