import sys
import pypandoc
from pathlib import Path

def build_resume(md_path, portrait_path):
    """Generate a resume PDF from markdown.
    """
    md_file = Path(md_path)
    portrait_file = Path(portrait_path)

    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    if not portrait_file.exists():
        raise FileNotFoundError(f"Portrait image not found: {portrait_path}")
        
    # Read the markdown content
    md_content = md_file.read_text(encoding='utf-8')
    
    # Create a temporary markdown file with modified content for better PDF generation
    temp_md_file = Path("temp_resume.md")
    
    # Process the markdown content to create a two-column layout for core competencies
    import re
    
    # Find the Core Competencies section
    competencies_section = re.search(r'# Core Competencies\s+([\s\S]+?)(?=\s+# Professional Experience)', md_content)
    
    if competencies_section:
        # Extract all competency items with their nested bullets
        competencies_text = competencies_section.group(1).strip()
        
        # Find all main competency items (lines starting with '- **')
        main_items_pattern = r'- \*\*(.*?)\*\*'
        main_competency_items = re.findall(main_items_pattern, competencies_text)
        
        # Process each main competency item and its nested items
        competency_blocks = []
        for i, item in enumerate(main_competency_items):
            # Find the start position of this competency item
            item_start = competencies_text.find(f'- **{item}**')
            
            # Find the end position (start of next item or end of section)
            if i < len(main_competency_items) - 1:
                next_item_start = competencies_text.find(f'- **{main_competency_items[i+1]}**', item_start)
                block_text = competencies_text[item_start:next_item_start].strip()
            else:
                # For the last item, go to the end of the competencies section
                block_text = competencies_text[item_start:].strip()
            
            competency_blocks.append(block_text)
        

        
        # Split into two halves for two columns
        half_point = len(competency_blocks) // 2
        first_half = competency_blocks[:half_point]
        second_half = competency_blocks[half_point:]
        
        # Format and escape LaTeX special characters in competency items
        escaped_items = []
        for block in first_half + second_half:
            # Replace LaTeX special characters
            escaped_block = block.replace('&', '\\&').replace('%', '\\%').replace('#', '\\#')
            
            # Extract the title (text between ** markers)
            title_match = re.search(r'- \*\*(.*?)\*\*', escaped_block)
            if title_match:
                title = title_match.group(1)
                
                # Find all nested bullet points - use a more robust pattern
                nested_items = re.findall(r'  - (.*?)(?=\n  -|\n\n|\n-|$)', escaped_block, re.DOTALL)
                nested_items = [item.strip() for item in nested_items if item.strip()]
                
                # Format with proper nested bullet styling
                nested_bullets = ''
                if nested_items:
                    nested_bullets = '\\begin{itemize}[leftmargin=1em,itemsep=0.05em,parsep=0.05em]\n'
                    for nested_item in nested_items:
                        nested_bullets += f'\\item {nested_item}\n'
                    nested_bullets += '\\end{itemize}'
                
                escaped_items.append(f'\\textbf{{{title}}} {nested_bullets}')
            
        # Replace the Core Competencies section with our custom formatted version
        # Remove the original header since our LaTeX command will add it
        modified_content = md_content.replace(
            competencies_section.group(0),
            "\\corecompetencies{\n" + 
            '\n'.join([f"\\item {item}" for item in escaped_items]) + 
            "\n}\n"
        )
        
        # Add page break before Professional Experience
        modified_content = modified_content.replace(
            "# Professional Experience",
            "\\pagebreak\n\n# Professional Experience"
        )
        
        # Write to temporary file
        temp_md_file.write_text(modified_content, encoding='utf-8')
    else:
        # If no Core Competencies section found, just use the original file
        temp_md_file.write_text(md_content, encoding='utf-8')
    
    # Create template for PDF generation
    template_path = Path("template.tex")
    template_content = f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{parskip}}
\\usepackage{{multicol}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}

% Define a command for tightlist since pandoc uses it
\\providecommand{{\\tightlist}}{{\\setlength{{\\itemsep}}{{0pt}}\\setlength{{\\parskip}}{{0pt}}}}

% Define column environment for core competencies
\\newenvironment{{competencycolumns}}{{
  \\begin{{multicols}}{{2}}
  \\setlength{{\\columnsep}}{{1cm}}
  \\setlength{{\\columnseprule}}{{0pt}}
}}{{\\end{{multicols}}}}

% Custom styles for resume sections
\\usepackage{{titlesec}}
\\titleformat{{\\section}}{{\\Large\\bfseries}}{{}}{{0em}}{{}}
\\titlespacing{{\\section}}{{0pt}}{{10pt}}{{5pt}}

% Custom command for core competencies section with proper bullet formatting
\\newcommand{{\\corecompetencies}}[1]{{
  \\section*{{Core Competencies}}
  \\begin{{multicols}}{{2}}
  \\small
  \\begin{{itemize}}[leftmargin=1em,itemsep=0.3em,parsep=0.15em]
    #1
  \\end{{itemize}}
  \\normalsize
  \\end{{multicols}}
}}

\\begin{{document}}

% Header with portrait and contact info
\\begin{{minipage}}{{0.25\\textwidth}}
  \\includegraphics[width=\\linewidth]{{{portrait_file.name}}}
\\end{{minipage}}%
\\hfill
\\begin{{minipage}}{{0.7\\textwidth}}
  \\Large \\textbf{{Micah Longmire}} \\\\
  \\normalsize Senior DevOps Engineer / Manager \\\\
  Roy, UT | mlmicahlongmire@gmail.com | github.com/bobbyhiddn | linkedin.com/in/micah-longmire
\\end{{minipage}}

\\vspace{{1em}}

$body$

\\end{{document}}
"""
    
    # Check if template exists and has the correct content
    should_write_template = True
    if template_path.exists():
        existing_content = template_path.read_text()
        if existing_content == template_content:
            should_write_template = False
    
    if should_write_template:
        template_path.write_text(template_content)

    # Copy portrait to current directory if needed
    target_path = Path.cwd() / portrait_file.name
    if portrait_file.resolve() != target_path.resolve():
        import shutil
        shutil.copy(portrait_file, target_path)

    # Check if template exists and has the correct content
    should_write_template = True
    if template_path.exists():
        existing_content = template_path.read_text(encoding='utf-8')
        if existing_content == template_content:
            should_write_template = False
    
    if should_write_template:
        template_path.write_text(template_content, encoding='utf-8')
    
    # Copy portrait to current directory if needed
    target_path = Path.cwd() / portrait_file.name
    if portrait_file.resolve() != target_path.resolve():
        import shutil
        shutil.copy(portrait_file, target_path)
    
    # Replace en spaces (U+2002) with regular spaces to avoid warnings
    if temp_md_file.exists():
        content = temp_md_file.read_text(encoding='utf-8')
        # Replace en space (U+2002) with regular space
        content = content.replace('\u2002', ' ')
        temp_md_file.write_text(content, encoding='utf-8')
    
    # Generate PDF
    output_file = Path("pdf/resume.pdf")
    pypandoc.convert_file(
        str(temp_md_file),
        to="pdf",
        outputfile=str(output_file),
        extra_args=[
            "--pdf-engine=xelatex",
            f"--template={template_path}",
            "--quiet"  # Suppress MiKTeX update warnings
        ]
    )
    
    # Clean up temporary file
    if temp_md_file.exists():
        temp_md_file.unlink()
    
    # Clean up temporary portrait file in current directory
    if Path(portrait_file.name).exists():
        Path(portrait_file.name).unlink()
    
    print(f"✅ Resume generated: {output_file.resolve()}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python build_resume.py <resume.md> <portrait.jpg>")
        sys.exit(1)
    
    build_resume(sys.argv[1], sys.argv[2])
