import sys
import pypandoc
from pathlib import Path

def build_resume(md_path, portrait_path):
    md_file = Path(md_path)
    portrait_file = Path(portrait_path)

    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    if not portrait_file.exists():
        raise FileNotFoundError(f"Portrait image not found: {portrait_path}")

    template_path = Path("template.tex")
    if not template_path.exists():
        template_path.write_text(f"""\
\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{parskip}}

% Define a command for tightlist since pandoc uses it
\\providecommand{{\\tightlist}}{{\\setlength{{\\itemsep}}{{0pt}}\\setlength{{\\parskip}}{{0pt}}}}

\\begin{{document}}

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
""")

    # 
    target_path = Path.cwd() / portrait_file.name
    if portrait_file.resolve() != target_path.resolve():
        import shutil
        shutil.copy(portrait_file, target_path)

    output_file = Path("resume.pdf")

    pypandoc.convert_file(
        str(md_file),
        to="pdf",
        outputfile=str(output_file),
        extra_args=[
            "--pdf-engine=xelatex",
            f"--template={template_path}"
        ]
    )

    print(f"✅ Resume generated: {output_file.resolve()}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python build_resume.py <resume.md> <portrait.jpg>")
        sys.exit(1)

    build_resume(sys.argv[1], sys.argv[2])

