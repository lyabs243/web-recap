from langchain_core.prompts import ChatPromptTemplate

from app.modules.recap.application.services.chains.models import QueryOutput
from app.modules.recap.application.services.prompts.query import QUERY_SYSTEM_PROMPT, QUERY_USER_PROMPT


def build_query_chain(model):
    prompt = ChatPromptTemplate.from_messages(
        [("system", QUERY_SYSTEM_PROMPT), ("human", QUERY_USER_PROMPT)]
    )
    return prompt | model.with_structured_output(QueryOutput)