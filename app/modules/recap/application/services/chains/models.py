from pydantic import BaseModel, Field


class QueryOutput(BaseModel):
    query: str = Field(min_length=3, max_length=160)


class CleanArticleOutput(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    cleaned_text: str = Field(min_length=50)


class SourcePlanOutput(BaseModel):
    article_title: str = Field(min_length=3, max_length=300)
    angle: str = Field(min_length=10, max_length=280)
    key_points: list[str] = Field(min_length=2, max_length=6)


class OutlineSectionOutput(BaseModel):
    heading: str = Field(min_length=3, max_length=120)
    purpose: str = Field(min_length=10, max_length=240)


class ArticleOutlineOutput(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    intro: str = Field(min_length=10, max_length=240)
    sections: list[OutlineSectionOutput] = Field(min_length=2, max_length=6)
    conclusion: str = Field(min_length=10, max_length=240)