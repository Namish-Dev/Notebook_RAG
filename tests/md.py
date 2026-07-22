import pymupdf4llm

pdf_path = r"C:\Users\hp\Downloads\Resume.pdf"

markdown = pymupdf4llm.to_markdown(pdf_path)

print(markdown)

# Optional: save to a file
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown)