import PyPDF2

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

pdf_path = r"c:\Users\Ramil\Downloads\QM\docs\DEVELOPMENT OF A ROAD ACCIDENT SIMULATION FOR AUTOMATIC ROAD ACCIDENT REPORT SYSTEM.pdf"
text = extract_text_from_pdf(pdf_path)
print(text)