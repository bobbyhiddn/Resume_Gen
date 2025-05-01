# Micah's Resume Generator

Hi, I'm Micah Longmire, a DevOps Engineer/Manager with a passion for automation, systems architecture, and creative problem-solving. This Resume Generator is part of my portfolio of hobby projects that showcase my approach to problem-solving through code. I believe that it is almost always the correct decision to generate solutions rather than click-ops them, even my resume.

Feel free to explore my other repositories to see more examples of my coding style and technical interests. I work on everything from and between CLI tools to full-stack CI/CD deployed iOS games.

## 📄 About This Project

A minimalist LaTeX-based resume generator that creates professional, beautifully formatted resumes from markdown content. The tool takes the pain out of resume formatting by handling the complex layout details for you.

### Features

- **Clean, Professional Formatting**: Customizable styling with LaTeX
- **Two-Column Layout**: For core competencies with nested bullet points
- **Automatic Page Breaks**: For better content organization
- **Portrait Integration**: Seamlessly includes your photo
- **Single Command Generation**: Simple CLI interface

## 🛠️ Requirements

- Python 3.6+
- Pandoc
- LaTeX distribution (e.g., MiKTeX, TeX Live)
- Python packages:
  - `pypandoc`

## 📥 Installation

1. Clone this repository:
   ```
   git clone https://github.com/bobbyhiddn/Resume_Gen.git
   cd Resume_Gen
   ```

2. Install Python dependencies:
   ```
   pip install pypandoc
   ```

3. Ensure you have Pandoc and a LaTeX distribution installed on your system.

## 🚀 Usage

1. Place your markdown resume in the `raw/` directory
2. Place your portrait photo in the `raw/` directory
3. Run the generator:

```
python build_resume.py raw/your_resume.md raw/your_portrait.jpg
```

The generated PDF will be saved to the `pdf/` directory.

## 📝 Markdown Format

Your markdown resume should follow this general structure:

```markdown
% Your Name % Your Title • Location | email | github | linkedin % Updated: Date

# Professional Summary

Your professional summary goes here...

# Core Competencies

- **Category Name**
  - Skill 1
  - Skill 2
  - Skill 3

- **Another Category**
  - Skill 1
  - Skill 2

# Professional Experience

## Job Title

**Company Name** – Location _(Start Date – End Date)_

- Achievement 1
- Achievement 2

# Education

- Degree, Institution, Year

# References

Available upon request.
```

## ⚙️ How It Works

The script processes your markdown resume by:

1. Parsing the core competencies section to create a two-column layout
2. Formatting nested bullet points with proper LaTeX styling
3. Adding your portrait to the header
4. Generating a professional PDF using Pandoc and LaTeX

## 🎨 Customization

The LaTeX template can be customized by modifying the `template_content` variable in `build_resume.py`. You can adjust:

- Font sizes and styles
- Margins and spacing
- Column widths
- Header and footer content

## 📂 Project Structure

```
Resume_Gen/
├── build_resume.py     # Main script
├── raw/                # Source files
│   ├── Resume.md       # Your markdown resume
│   └── Portrait.jpg    # Your portrait photo
├── pdf/                # Output directory
│   └── resume.pdf      # Generated resume
└── README.md           # This file
```

## 📜 License

This project is open source and available under the MIT License.

Created by Micah Longmire ([GitHub](https://github.com/bobbyhiddn))