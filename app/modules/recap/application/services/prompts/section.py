SECTION_WRITER_SYSTEM_PROMPT = """
You write one section of a synthesized recap article.
Use only the supplied source evidence.
Avoid unsupported claims and avoid mentioning that the text was AI-generated.
Write in the requested language.
""".strip()

SECTION_WRITER_USER_PROMPT = """
Language: {language}
Article title: {article_title}
Section heading: {heading}
Section purpose: {purpose}
Intro objective: {intro}
Conclusion objective: {conclusion}

Evidence:
{evidence}

Write only the section body in Markdown, starting with a level-2 heading.
""".strip()