import markdown
import os
import sys

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint not available: {e}. Falling back to HTML.")

def convert_md_to_pdf(md_file, output_pdf):
    with open(md_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(text, extensions=['extra', 'codehilite', 'tables', 'toc'])

    # Basic CSS for better PDF rendering
    css_content = """
    body { font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.6; font-size: 12px; margin: 40px; }
    h1, h2, h3 { color: #2c3e50; page-break-after: avoid; }
    h1 { font-size: 24px; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }
    h2 { font-size: 20px; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 30px; }
    code { font-family: 'Courier New', monospace; background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
    pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px; overflow-x: auto; page-break-inside: avoid; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    blockquote { border-left: 4px solid #ddd; padding-left: 15px; color: #777; font-style: italic; }
    .mermaid { display: none; } /* Hide mermaid code in PDF if not rendered */
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>{css_content}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    if WEASYPRINT_AVAILABLE:
        try:
            print(f"Generating PDF: {output_pdf}...")
            HTML(string=full_html).write_pdf(output_pdf)
            print("PDF generation successful.")
        except Exception as e:
            print(f"PDF generation failed: {e}")
            # Fallback to saving HTML
            html_file = output_pdf.replace('.pdf', '.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"Saved as HTML instead: {html_file}")
    else:
        # Save as HTML
        html_file = output_pdf.replace('.pdf', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"Saved as HTML (PDF tools missing): {html_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_guide_to_pdf.py <md_file> [output_pdf]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.pdf')
    
    convert_md_to_pdf(md_file, output_pdf)
