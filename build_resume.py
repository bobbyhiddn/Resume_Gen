#!/usr/bin/env python3
"""Build a resume PDF from markdown and a JPEG portrait."""

import re
import shutil
import sys
from pathlib import Path

import pypandoc

JPEG_MAGIC = b"\xff\xd8\xff"


def assert_jpeg(portrait_file: Path) -> None:
    """Fail if the portrait is not a real JPEG.

    A previous upload stored raw/Portrait.jpg as base64 text. The build used
    to decode that in place. It now requires binary JPEG bytes so a bad
    portrait cannot pass silently.
    """
    data = portrait_file.read_bytes()
    if len(data) < 3 or not data.startswith(JPEG_MAGIC):
        raise ValueError(
            f"Portrait is not a JPEG image: {portrait_file}. "
            "Expected binary JPEG data beginning with FFD8FF. "
            "Base64 text and other non-image encodings are not accepted."
        )


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def parse_header(md_content: str):
    metadata_match = re.match(r"^% (.+)\n% (.+)\n% (.+)", md_content)
    if not metadata_match:
        return (
            "Micah Longmire",
            "Program Technical Lead / AI & Automation Product Manager",
            "Roy, UT | mlmicahlongmire@gmail.com | github.com/bobbyhiddn | linkedin.com/in/micah-longmire",
        )

    author_name = metadata_match.group(1).strip()
    title_line = metadata_match.group(2).strip()
    if "•" in title_line:
        title, contact_info = (part.strip() for part in title_line.split("•", 1))
    else:
        title = title_line
        contact_info = (
            "Roy, UT | mlmicahlongmire@gmail.com | "
            "github.com/bobbyhiddn | linkedin.com/in/micah-longmire"
        )
    return author_name, title, contact_info


def format_contact(contact_info: str) -> str:
    """Wrap contact details into two ragged lines instead of one justified line."""
    parts = [latex_escape(part.strip()) for part in contact_info.split("|") if part.strip()]
    if not parts:
        return latex_escape(contact_info)
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] + r" \\ " + parts[1]
    line_one = parts[0] + " | " + parts[1]
    line_two = " | ".join(parts[2:])
    return line_one + r" \\ " + line_two


def format_competency_block(block: str) -> str:
    escaped = (
        block.replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
    )
    title_match = re.search(r"- \*\*(.*?)\*\*", escaped)
    if not title_match:
        return ""
    comp_title = title_match.group(1)
    nested_items = re.findall(r"  - (.*?)(?=\n  -|\n\n|\n-|$)", escaped, re.DOTALL)
    nested_items = [item.strip() for item in nested_items if item.strip()]
    nested = ""
    if nested_items:
        nested = (
            "\\begin{itemize}[leftmargin=1em,itemsep=1pt,parsep=0pt,topsep=1pt,partopsep=0pt]\n"
            + "".join(f"\\item {item}\n" for item in nested_items)
            + "\\end{itemize}"
        )
    # The whole category, including its sub-bullets, is one unbreakable box.
    return (
        "\\noindent\\begin{minipage}{\\linewidth}\n"
        "\\raggedright\n"
        "\\hyphenpenalty=10000\n"
        "\\exhyphenpenalty=10000\n"
        "\\begin{itemize}[leftmargin=1.15em,itemsep=2pt,parsep=0pt,topsep=1pt,partopsep=0pt]\n"
        f"\\item \\textbf{{{comp_title}}}{nested}\n"
        "\\end{itemize}\n"
        "\\end{minipage}\\par\\vspace{0.28em}\n"
    )


def rewrite_competencies(md_content: str) -> str:
    competencies_section = re.search(
        r"# Core Competencies\s+([\s\S]+?)(?=\s+# Professional Experience)",
        md_content,
    )
    if not competencies_section:
        return md_content

    competencies_text = competencies_section.group(1).strip()
    main_items = re.findall(r"- \*\*(.*?)\*\*", competencies_text)
    blocks = []
    for index, item in enumerate(main_items):
        item_start = competencies_text.find(f"- **{item}**")
        if index < len(main_items) - 1:
            next_start = competencies_text.find(
                f"- **{main_items[index + 1]}**", item_start
            )
            block_text = competencies_text[item_start:next_start].strip()
        else:
            block_text = competencies_text[item_start:].strip()
        formatted = format_competency_block(block_text)
        if formatted:
            blocks.append(formatted)

    replacement = "\\corecompetencies{%\n" + "".join(blocks) + "}\n"
    return md_content.replace(competencies_section.group(0), replacement)


def render_template(author: str, title: str, contact: str, portrait_name: str) -> str:
    template_path = Path("template.tex")
    if not template_path.exists():
        raise FileNotFoundError(f"LaTeX template not found: {template_path}")
    template = template_path.read_text(encoding="utf-8")
    required = ("@@AUTHOR@@", "@@TITLE@@", "@@CONTACT@@", "@@PORTRAIT@@", "$body$")
    missing = [token for token in required if token not in template]
    if missing:
        raise ValueError(
            "template.tex is missing required placeholders: " + ", ".join(missing)
        )
    if not re.fullmatch(r"[\w./-]+", portrait_name):
        raise ValueError(f"Portrait filename is not safe to embed in LaTeX: {portrait_name}")
    return (
        template.replace("@@AUTHOR@@", latex_escape(author))
        .replace("@@TITLE@@", latex_escape(title))
        .replace("@@CONTACT@@", contact)
        .replace("@@PORTRAIT@@", portrait_name)
    )


def find_latest_resume(raw_dir: Path) -> Path:
    """Pick the newest resume without trusting file mtimes.

    A fresh checkout stamps every file with the same mtime, so ``ls -t`` is
    not a stable way to choose among raw/*.md. Prefer the pandoc ``Updated:``
    date, then a date encoded in the filename, then the filename itself.
    """
    files = sorted(path for path in Path(raw_dir).glob("*.md") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No resume markdown found in {raw_dir}")

    def sort_key(path: Path):
        text = path.read_text(encoding="utf-8", errors="replace")
        updated = (0, 0, 0)
        updated_match = re.search(
            r"^%\s*Updated:\s*(\d{4})-(\d{2})-(\d{2})",
            text,
            re.MULTILINE,
        )
        if updated_match:
            updated = tuple(int(part) for part in updated_match.groups())

        file_date = (0, 0, 0)
        iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", path.stem)
        us = re.search(r"(\d{1,2})-(\d{1,2})-(\d{2,4})$", path.stem)
        if iso:
            file_date = tuple(int(part) for part in iso.groups())
        elif us:
            month, day, year = (int(part) for part in us.groups())
            if year < 100:
                year += 2000
            file_date = (year, month, day)
        return (updated, file_date, path.name)

    return max(files, key=sort_key)


def build_resume(md_path, portrait_path):
    md_file = Path(md_path)
    portrait_file = Path(portrait_path)

    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    if not portrait_file.exists():
        raise FileNotFoundError(f"Portrait image not found: {portrait_path}")
    assert_jpeg(portrait_file)

    md_content = md_file.read_text(encoding="utf-8").replace("\u2002", " ")
    author_name, title, contact_info = parse_header(md_content)
    modified_content = rewrite_competencies(md_content)

    temp_md = Path("temp_resume.md")
    temp_template = Path("temp_template.tex")
    copied_portrait = None
    try:
        temp_md.write_text(modified_content, encoding="utf-8")
        temp_template.write_text(
            render_template(
                author_name,
                title,
                format_contact(contact_info),
                portrait_file.name,
            ),
            encoding="utf-8",
        )

        target = Path.cwd() / portrait_file.name
        if portrait_file.resolve() != target.resolve():
            shutil.copy(portrait_file, target)
            copied_portrait = target

        output_file = Path("pdf/resume.pdf")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pypandoc.convert_file(
            str(temp_md),
            to="pdf",
            outputfile=str(output_file),
            extra_args=[
                "--pdf-engine=xelatex",
                f"--template={temp_template}",
                "--quiet",
            ],
        )
    finally:
        if temp_md.exists():
            temp_md.unlink()
        if temp_template.exists():
            temp_template.unlink()
        if copied_portrait is not None and copied_portrait.exists():
            copied_portrait.unlink()

    print(f"Resume generated: {output_file.resolve()}")


def main(argv):
    if len(argv) == 3 and argv[1] == "--latest":
        print(find_latest_resume(Path(argv[2])).as_posix())
        return 0
    if len(argv) != 3:
        print("Usage: python build_resume.py <resume.md> <portrait.jpg>")
        print("       python build_resume.py --latest <raw-directory>")
        return 1
    build_resume(argv[1], argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
