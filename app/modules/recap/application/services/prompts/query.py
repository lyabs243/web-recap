QUERY_SYSTEM_PROMPT = """
You create compact news search queries.
Return a query that maximizes relevant current-news coverage for the requested topic.
Respect the requested language.

CONTEXT: The current date is {current_date}. 
Only specify a year if it is the current year or relevant to the specific historical context of the topic.
""".strip()

QUERY_USER_PROMPT = """
Topic: {topic}
Language: {language}
Current Date: {current_date}

Create a short search-engine query aimed at recent news coverage.
""".strip()
