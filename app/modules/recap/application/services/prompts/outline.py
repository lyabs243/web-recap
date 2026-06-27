SOURCE_PLAN_SYSTEM_PROMPT = """
You extract the reporting angle and main points from a single news article.
Return concise structured output.
""".strip()

SOURCE_PLAN_USER_PROMPT = """
Topic: {topic}
Language: {language}
Article title: {title}

Article text:
{text}
""".strip()

ARTICLE_OUTLINE_SYSTEM_PROMPT = """
You are planning a recap article synthesized from multiple news sources.
Create a clear title, a short introduction, a section plan, and a conclusion.
The introduction and conclusion should be the final text, not just objectives.
Do not repeat the article title in the introduction.
""".strip()

ARTICLE_OUTLINE_USER_PROMPT = """
Topic: {topic}
Language: {language}

Source evidence:
{evidence}
""".strip()