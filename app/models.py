from typing import List, Optional
from fastapi.datastructures import UploadFile
from pydantic.main import BaseModel
from enum import Enum


class BaseResponse(BaseModel):
    error: Optional[str] = None


class ExtractorRequest(BaseModel):
    url: Optional[str] = None
    filename: Optional[str] = None
    meta: Optional[dict] = None

    extractor: Optional[str] = None
    config: Optional[dict] = None


class ExtractorResponse(BaseResponse):
    meta: Optional[dict] = None
    text: str = ""
    embedded_objects: Optional[List[dict]] = None


class PipelineExecutionRequest(BaseModel):
    """
    Execution request object for a pipeline. Currently accept either a plain text input, or a public URL.
    In case of an URL, we'll delegate to UniversalExtractor first to extract the text/metadata,
    before feeding them into the NLP pipeline.
    (if it's of a recognized format like .pdf, .docx etc.)
    Optional settings will be handed down to the pipeline implementation to make sense of it
    """

    text: Optional[str] = None
    url: Optional[str] = None
    meta: Optional[dict] = None
    settings: Optional[dict] = None


class PipelineExecutionResponse(BaseModel):
    text: Optional[str] = None
    meta: Optional[dict] = {}


class ImmersiveReaderTokenResponse(BaseModel):
    token: str
    subdomain: str


class DefinitionResponse(BaseModel):
    term: str
    definitions: Optional[list]


# TAH = (Azure) Text Analytics for Health
class TAHRequestDocument(BaseModel):
    language: Optional[str] = "en"
    id: Optional[int] = 1
    text: str


class TAHResponseDocument(BaseModel):
    entities: List[dict]


class AnalyzeRequest(BaseModel):
    documents: List[TAHRequestDocument]


#
# Known document-level pipeline stage names.
# Per convention, these are used as names when adding/removing/disabling pipes.
# Our custom pipes also use this name to register doc extensions, e.g. their data will be available under
#   doc._.<STAGE_NAME>
#
class PIPELINE_STAGES(object):
    CLEANER = "cleaner"
    TAGGER = "tagger"
    PARSER = "parser"
    SENTENCIZER = "sentencizer"
    SUMMARIZER = "summarizer"
    ROUGE_SCORER = "rouge_scorer"
    NER = "ner"
    MERGE_NOUN_CHUNKS = "merge_noun_chunks"
    MERGE_ENTITIES = "merge_entities"
    HEALTH_ANALYZER = "health_analyzer"
    READABILITY = "readability"
    REPORT_COLLECTOR = "report_collector"
    STORY_GENERATOR = "story_generator"
