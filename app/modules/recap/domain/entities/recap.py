from dataclasses import dataclass, field
from typing import Literal


LanguageCode = Literal["en", "fr"]


@dataclass(frozen=True)
class RecapRequest:
    topic: str
    language: LanguageCode
    max_results: int = 5


@dataclass(frozen=True)
class SearchReference:
    title: str
    url: str
    snippet: str
    favicon_url: str
    source: str


@dataclass(frozen=True)
class SourceArticle:
    url: str
    search_title: str
    extracted_title: str
    cleaned_text: str
    snippet: str
    favicon_url: str
    source: str


@dataclass(frozen=True)
class SourcePlan:
    article_title: str
    angle: str
    key_points: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OutlineSection:
    heading: str
    purpose: str


@dataclass(frozen=True)
class RecapOutline:
    title: str
    intro: str
    sections: list[OutlineSection]
    conclusion: str


@dataclass(frozen=True)
class GeneratedSection:
    heading: str
    markdown: str


@dataclass(frozen=True)
class RecapDocument:
    title: str
    markdown: str
    references: list[SearchReference]