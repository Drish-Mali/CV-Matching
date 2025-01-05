
import pdfplumber
from pathlib import Path
from typing import Optional, Tuple

def clean_text(text: str, lower_case: bool) -> str:
    """
    Cleans text by performing several pre-processing steps.
    Args:
        text (str): The input text to be cleaned.
        lower_case (bool): If True, the text is converted to lowercase.
    Returns:
        str: The cleaned text.
    """
    if lower_case:
        text = text.lower()
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines)

def extract_table_data(page) -> Optional[str]:
    """
    Extracts table data from a page.
    Args:
        page: A pdfplumber page object.
    Returns:
        Optional[str]: The extracted table data as a string or None if no table is found.
    """
    table = page.extract_table()
    if table:
        try:
            cleaned_rows = ["\t".join(cell or "" for cell in row) for row in table]
            return "\n".join(cleaned_rows)
        except Exception as e:
            print(f"Error extracting table: {e}")
    return None

def extract_text_with_alignment(page) -> str:
    """
    Extracts text from a page, aligning words based on their Y-coordinates 
    to preserve structure better.
    Args:
        page: A pdfplumber page object.
    Returns:
        str: The aligned text extracted from the page.
    """
    words = page.extract_words()
    lines = {}

    for word in words:
        y_coord = round(word["top"])  # Round to group nearby words
        if y_coord not in lines:
            lines[y_coord] = []
        lines[y_coord].append(word["text"])

    # Sort by Y-coordinates and join words into lines
    sorted_lines = sorted(lines.items())
    aligned_text = "\n".join(" ".join(words) for _, words in sorted_lines)
    return aligned_text

def extract_text_and_tables(file_path: str, lower_case: bool) -> Tuple[int, int, str]:
    """
    Extracts text and tables using alignment-based logic to preserve key-value structure.
    Also returns the number of pages and the character count of the extracted content.
    
    Args:
        file_path (str): The file path of the PDF.
        lower_case (bool): Whether or not to convert the text to lowercase before cleaning.
    
    Returns:
        tuple: A tuple containing the number of pages (int), total character count (int), and the extracted content (str).
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            all_content = []

            for page in pdf.pages:
                # Use alignment-based text extraction
                page_text = extract_text_with_alignment(page)

                # Extract table data if present
                table_data = extract_table_data(page)
                if table_data:
                    page_text += f"\n\n---TABLE DATA---\n{table_data}"

                all_content.append(page_text)

            # Combine all pages and clean the text
            full_text = "\n---PAGE BREAK---\n".join(all_content)
            cleaned_text = clean_text(full_text, lower_case)

            # Get number of pages and character count
            num_pages = len(pdf.pages)
            char_count = len(cleaned_text)

            return num_pages, char_count, cleaned_text

    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def process_single_file(file_path: str, lower_case: bool) -> None:
    """
    Process a single PDF file, display its contents, page count, and character count.
    
    Args:
        file_path (str): Path to the PDF file.
        lower_case (bool): Whether to convert text to lowercase.
    """
    try:
        num_pages, char_count, extracted_content = extract_text_and_tables(file_path, lower_case)
        
        print(f"Document Info:\n- Number of Pages: {num_pages}\n- Character Count: {char_count}\n")
        print("Extracted Content:\n")
        return extracted_content
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None
