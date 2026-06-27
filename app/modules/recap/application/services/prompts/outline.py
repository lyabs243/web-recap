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
Create a clear title, a short introduction objective, a section plan, and a conclusion objective.
""".strip()

ARTICLE_OUTLINE_USER_PROMPT = """
Topic: {topic}
Language: {language}

Source evidence:
{evidence}
""".strip()