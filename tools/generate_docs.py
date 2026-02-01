import markdown
import os

def convert_md_to_html(md_file, html_file):
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Add some basic CSS for better readability
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; color: #24292e; }}
                pre {{ background: #f6f8fa; padding: 16px; border-radius: 6px; overflow: auto; }}
                code {{ font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; background: rgba(27,31,35,0.05); padding: 0.2em 0.4em; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; }}
                th {{ background: #f6f8fa; }}
                blockquote {{ border-left: 0.25em solid #dfe2e5; color: #6a737d; padding: 0 1em; margin: 0; }}
            </style>
        </head>
        <body>
        {markdown.markdown(text, extensions=['tables', 'fenced_code'])}
        </body>
        </html>
        """
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Successfully converted {md_file} to {html_file}")
    except Exception as e:
        print(f"Error converting {md_file}: {e}")

if __name__ == "__main__":
    convert_md_to_html('docs/mimari_tasarim.md', 'docs/mimari_tasarim.html')
    convert_md_to_html('docs/DEPLOYMENT_TR.md', 'docs/DEPLOYMENT_TR.html')
