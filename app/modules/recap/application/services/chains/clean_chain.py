from langchain_core.prompts import ChatPromptTemplate

from app.modules.recap.application.services.chains.models import CleanArticleOutput
from app.modules.recap.application.services.prompts.clean import CLEAN_SYSTEM_PROMPT, CLEAN_USER_PROMPT


def build_clean_chain(model):
    prompt = ChatPromptTemplate.from_messages(
        [("system", CLEAN_SYSTEM_PROMPT), ("human", CLEAN_USER_PROMPT)]
    )
    return prompt | model.with_structured_output(CleanArticleOutput)