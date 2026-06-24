#!/usr/bin/env python3
"""
generate_html.py
Parse resume.tex -> generate index.html, preserving the existing CSS design.
Usage: python3 generate_html.py [resume.tex] [index.html]
"""

import re
import sys

# --- Hardcoded personal info (rarely changes) --------------------------------
NAME         = "Adam O'Brien, PhD"
EMAIL        = "obrienadam89@gmail.com"
PHONE        = "(603) 266-7012"
PHONE_HREF   = "tel:+16032667012"
LOCATION     = "Mountain View, CA"
GITHUB_URL   = "https://github.com/obrienadam"
LINKEDIN_URL = "https://www.linkedin.com/in/obrien-adam/"
SUBTITLE     = "High-Performance Computing \u2022 Low-Latency ML Infrastructure \u2022 Numerical Simulation"
PDF_FILE     = "resume.pdf"
PDF_DOWNLOAD = "Adam_OBrien_Resume.pdf"
META_DESC    = (
    f"Resume of {NAME} - Software Engineer specializing in "
    "Machine Learning Infrastructure, JAX/XLA, and High-Performance Numerical Computing."
)

# --- SVG icons (static) ------------------------------------------------------
SVG_DOWNLOAD = (
    '<svg viewBox="0 0 24 24">'
    '<path d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2z'
    "m-6 .67l2.59-2.58L17 11.5l-5 5-5-5 1.41-1.41L11 12.67V3h2v9.67z\"/></svg>"
)
SVG_EMAIL = (
    '<svg class="icon" viewBox="0 0 24 24">'
    '<path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6'
    "c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z\"/></svg>"
)
SVG_PHONE = (
    '<svg class="icon" viewBox="0 0 24 24">'
    '<path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 '
    "1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 "
    "0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 "
    "1.02l-2.2 2.2z\"/></svg>"
)
SVG_LOCATION = (
    '<svg class="icon" viewBox="0 0 24 24" style="color: var(--text-muted);">'
    '<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z'
    "m0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z\"/></svg>"
)
SVG_GITHUB = (
    '<svg class="icon" viewBox="0 0 24 24">'
    '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385'
    ".6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61"
    "C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 "
    "1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305"
    ".76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22"
    "-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 "
    "3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23"
    ".645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 "
    "5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 "
    "0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12\"/></svg>"
)
SVG_LINKEDIN = (
    '<svg class="icon" viewBox="0 0 24 24">'
    '<path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14'
    "c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11z"
    "m-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 "
    "1.75.779 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604"
    "c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 "
    "7-2.777 7 2.476v6.759z\"/></svg>"
)


# --- LaTeX brace extraction ---------------------------------------------------

def extract_braced(text, start):
    """
    Return (content, end_index) for the {...} block beginning at `start`.
    Handles arbitrarily nested braces.
    """
    if start >= len(text) or text[start] != '{':
        raise ValueError(
            f"Expected '{{' at pos {start}, got {text[start:start+20]!r}"
        )
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
    raise ValueError("Unmatched '{' in LaTeX source")


# --- LaTeX -> HTML text conversion -------------------------------------------

def latex_to_html(text):
    """Convert a LaTeX string to an HTML string."""
    result = []
    i = 0
    while i < len(text):
        # Em dash / en dash
        if text[i:i+3] == '---':
            result.append('\u2014')
            i += 3
            continue
        if text[i:i+2] == '--':
            result.append('\u2013')
            i += 2
            continue

        # LaTeX directional quotes
        if text[i:i+2] == '``':
            result.append('\u201c')
            i += 2
            continue
        if text[i:i+2] == "''":
            result.append('\u201d')
            i += 2
            continue

        # Double backslash (line break) -> space
        if text[i:i+2] == '\\\\':
            result.append(' ')
            i += 2
            continue

        # LaTeX commands
        if text[i] == '\\':
            j = i + 1
            # Single-character special escapes
            if j < len(text) and text[j] in '&$%~{}#_':
                special = text[j]
                mapping = {'&': '&amp;', '$': '$', '%': '%',
                           '~': '~', '{': '{', '}': '}', '#': '#', '_': '_'}
                result.append(mapping.get(special, special))
                i = j + 1
                continue

            # Multi-character command name
            cmd_start = j
            while j < len(text) and text[j].isalpha():
                j += 1
            cmd = text[cmd_start:j]

            # Optional star suffix
            if j < len(text) and text[j] == '*':
                j += 1
            # Skip spaces between command and argument
            while j < len(text) and text[j] in ' \t':
                j += 1

            if cmd == 'textbf':
                content, j = extract_braced(text, j)
                result.append(f'<strong>{latex_to_html(content)}</strong>')
            elif cmd == 'textit':
                content, j = extract_braced(text, j)
                result.append(f'<em>{latex_to_html(content)}</em>')
            elif cmd == 'href':
                url, j = extract_braced(text, j)
                link_text, j = extract_braced(text, j)
                result.append(f'<a href="{url}">{latex_to_html(link_text)}</a>')
            elif cmd == 'textasciitilde':
                result.append('~')
            elif cmd in ('noindent', 'hfill', 'small', 'large', 'vspace',
                         'pagestyle', 'bfseries', 'Huge', 'normalsize',
                         'vspace', 'setlist', 'titleformat', 'titlespacing'):
                # Silently consume optional brace argument
                if j < len(text) and text[j] == '{':
                    _, j = extract_braced(text, j)
            else:
                # Unknown command: render braced argument if present, else skip
                if j < len(text) and text[j] == '{':
                    content, j = extract_braced(text, j)
                    result.append(latex_to_html(content))

            i = j
            continue

        # Bare braces used for LaTeX grouping
        if text[i] == '{':
            content, j = extract_braced(text, i)
            result.append(latex_to_html(content))
            i = j
            continue
        if text[i] == '}':
            i += 1  # stray closing brace
            continue

        # Inline math $...$
        if text[i] == '$':
            end = text.find('$', i + 1)
            if end != -1:
                math = text[i + 1:end].replace('\\cdot', '\u00b7')
                result.append(math)
                i = end + 1
            else:
                result.append('$')
                i += 1
            continue

        # Non-breaking space shorthand
        if text[i] == '~':
            result.append(' ')
            i += 1
            continue

        result.append(text[i])
        i += 1

    return ''.join(result).strip()


# --- LaTeX document parsing --------------------------------------------------

def strip_comments(latex):
    """Remove LaTeX line comments (% ... to end of line)."""
    return re.sub(r'%[^\n]*', '', latex)


def parse_section(latex, section_name):
    """Return raw LaTeX content for a named section."""
    pattern = (
        r'\\section\{' + re.escape(section_name) + r'\}'
        r'(.*?)(?=\\section\{|\\end\{document\})'
    )
    m = re.search(pattern, latex, re.DOTALL)
    return m.group(1).strip() if m else ''


def parse_resume_items(block):
    """Return list of raw LaTeX strings from \\resumeItem{...} calls."""
    items = []
    i = 0
    while True:
        idx = block.find('\\resumeItem', i)
        if idx == -1:
            break
        brace = block.find('{', idx)
        if brace == -1:
            break
        content, end = extract_braced(block, brace)
        items.append(content)
        i = end
    return items


def parse_work_experience(section_content):
    """Return list of dicts: {company, location, role, dates, items}."""
    heading_re = re.compile(
        r'\\resumeHeading\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}',
        re.DOTALL,
    )
    parts = heading_re.split(section_content)
    experiences = []
    i = 1
    while i + 4 <= len(parts):
        company  = parts[i].strip()
        location = parts[i + 1].strip()
        role     = parts[i + 2].strip()
        dates    = parts[i + 3].strip()
        content  = parts[i + 4] if i + 4 < len(parts) else ''
        env = re.search(
            r'\\begin\{itemize\}(.*?)\\end\{itemize\}', content, re.DOTALL
        )
        items = parse_resume_items(env.group(1)) if env else []
        experiences.append(
            dict(company=company, location=location,
                 role=role, dates=dates, items=items)
        )
        i += 5
    return experiences


def parse_education(section_content):
    """Return dict with institution, location, degree, dates, items."""
    inst_m = re.search(
        r'\\textbf\{([^}]+)\}\s*\\hfill\s*([^\\]+)', section_content
    )
    deg_m = re.search(
        r'\\textit\{([^}]+)\}\s*\\hfill\s*([^\\]+)', section_content
    )
    env = re.search(
        r'\\begin\{itemize\}(.*?)\\end\{itemize\}', section_content, re.DOTALL
    )
    return {
        'institution': inst_m.group(1).strip() if inst_m else '',
        'location':    inst_m.group(2).strip() if inst_m else '',
        'degree':      deg_m.group(1).strip()  if deg_m  else '',
        'dates':       deg_m.group(2).strip()  if deg_m  else '',
        'items':       parse_resume_items(env.group(1)) if env else [],
    }


def parse_skills(section_content):
    """Return list of (category_name, [skill, ...]) tuples."""
    skills = []
    pattern = re.compile(
        r'\\noindent\\textbf\{([^}]+)\}\s*(.*?)(?=\\noindent|$)',
        re.DOTALL,
    )
    for m in pattern.finditer(section_content):
        category = m.group(1).rstrip(':').replace('\\&', '&').strip()
        raw      = m.group(2).strip().rstrip('\\').strip()
        skill_list = [latex_to_html(s.strip()) for s in raw.split(',') if s.strip()]
        if skill_list:
            skills.append((category, skill_list))
    return skills


# --- HTML rendering ----------------------------------------------------------

# Matches \textbf{Category name:} at item start — colon may be inside or outside braces
_CATEGORY_RE = re.compile(r'^\s*\\textbf\{([^}]+)\}\s*(.*)', re.DOTALL)


def render_exp_items(items):
    """Render a list of resumeItem strings into HTML bullet structure."""
    has_cats = any(_CATEGORY_RE.match(it) for it in items)
    lines = []

    if has_cats:
        lines.append('          <ul>')
        for item in items:
            m = _CATEGORY_RE.match(item)
            if m:
                # Strip trailing colon from category name (colon may be inside braces)
                cat   = latex_to_html(m.group(1).strip().rstrip(':'))
                body  = latex_to_html(m.group(2).strip())
                lines += [
                    '            <li>',
                    f'              <div class="category-title">{cat}</div>',
                    '              <ul class="exp-bullets">',
                    f'                <li>{body}</li>',
                    '              </ul>',
                    '            </li>',
                ]
            else:
                lines.append(f'            <li>{latex_to_html(item)}</li>')
        lines.append('          </ul>')
    else:
        lines.append('          <ul class="exp-bullets">')
        for item in items:
            lines.append(f'            <li>{latex_to_html(item)}</li>')
        lines.append('          </ul>')

    return '\n'.join(lines)


def render_education(edu):
    dates = latex_to_html(edu['dates'])
    if not edu['items']:
        notes_html = ''
    else:
        notes_html = '          <ul style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem; padding-left: 1.2rem;">\n'
        for it in edu['items']:
            notes_html += f'            <li style="margin-bottom: 0.25rem;">{latex_to_html(it)}</li>\n'
        notes_html += '          </ul>'

    return (
        '      <section id="education">\n'
        '        <h2>Education</h2>\n'
        '        <div class="edu-item">\n'
        '          <div class="edu-header">\n'
        f'            <strong>{edu["institution"]}</strong>\n'
        '          </div>\n'
        f'          <div class="degree">{edu["degree"]}</div>\n'
        f'          <div class="date">{dates}</div>\n'
f'{notes_html}\n'
        '        </div>\n'
        '      </section>'
    )


def render_skills(skills):
    lines = []
    for category, items in skills:
        lines += [
            '        <div class="skills-group">',
            f'          <h3>{category}</h3>',
            '          <div class="skills-list">',
        ]
        for item in items:
            lines.append(f'            <span class="skill-tag">{item}</span>')
        lines += ['          </div>', '        </div>', '']
    return '\n'.join(lines)


# --- Full HTML assembly -------------------------------------------------------

def generate_html(latex):
    latex        = strip_comments(latex)
    summary_html = latex_to_html(parse_section(latex, 'Summary'))
    experiences  = parse_work_experience(parse_section(latex, 'Work Experience'))
    education    = parse_education(parse_section(latex, 'Education'))
    skills       = parse_skills(parse_section(latex, 'Technical Skills'))

    exp_blocks = []
    for idx, exp in enumerate(experiences):
        extra    = ' page-break' if idx == 1 else ''
        role_str = f"{latex_to_html(exp['role'])} | {latex_to_html(exp['location'])}"
        exp_blocks.append(
            f'        <div class="exp-item{extra}">\n'
            f'          <div class="exp-header">\n'
            f'            <span class="company">{latex_to_html(exp["company"])}</span>\n'
            f'            <span class="date">{latex_to_html(exp["dates"])}</span>\n'
            f'          </div>\n'
            f'          <div class="role">{role_str}</div>\n'
            f'{render_exp_items(exp["items"])}\n'
            f'        </div>'
        )
    exp_html    = '\n\n'.join(exp_blocks)
    edu_html    = render_education(education)
    skills_html = render_skills(skills)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{META_DESC}">
  <title>{NAME} - Resume</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <header>
      <div class="header-top">
        <div>
          <h1 id="candidate-name">{NAME}</h1>
          <div class="subtitle">{SUBTITLE}</div>
        </div>
        <a id="download-pdf-btn" class="download-btn" href="{PDF_FILE}" download="{PDF_DOWNLOAD}">
          {SVG_DOWNLOAD}
          Download PDF
        </a>
      </div>
      <div class="contact-info">
        <span>
          <a href="mailto:{EMAIL}" aria-label="Email">
            {SVG_EMAIL}
            {EMAIL}
          </a>
        </span>
        <span>
          <a href="{PHONE_HREF}" aria-label="Phone">
            {SVG_PHONE}
            {PHONE}
          </a>
        </span>
        <span>
          <span style="display: inline-flex; align-items: center; gap: 0.35rem;">
            {SVG_LOCATION}
            {LOCATION}
          </span>
        </span>
        <span>
          <a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer" aria-label="GitHub" class="social-glyph">
            {SVG_GITHUB}
          </a>
        </span>
        <span>
          <a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn" class="social-glyph">
            {SVG_LINKEDIN}
          </a>
        </span>
      </div>
    </header>

    <div class="main-col">
      <section id="summary">
        <h2>Summary</h2>
        <p class="summary-text">
          {summary_html}
        </p>
      </section>

      <section id="experience">
        <h2>Work Experience</h2>

{exp_html}
      </section>
    </div>

    <div class="sidebar-col">
{edu_html}

      <section id="skills">
        <h2>Skills</h2>

{skills_html}      </section>
    </div>
  </div>
</body>
</html>
"""


# --- Entry point -------------------------------------------------------------

def main():
    input_file  = sys.argv[1] if len(sys.argv) > 1 else 'resume.tex'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'index.html'

    with open(input_file, 'r', encoding='utf-8') as f:
        latex = f.read()

    html = generate_html(latex)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated {output_file} from {input_file}", file=sys.stderr)


if __name__ == '__main__':
    main()
