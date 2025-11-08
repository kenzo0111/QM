import PyPDF2

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

pdf_path = r"c:\Users\Ramil\Downloads\QM\docs\Simulation_RoadAccident_InLabo (1).pdf"
text = extract_text_from_pdf(pdf_path)
print(text)