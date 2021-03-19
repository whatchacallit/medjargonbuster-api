# Basic imports
import os, json, logging, tempfile
from dotenv import load_dotenv, find_dotenv

# Init logging
import logging

import requests


log = logging.getLogger(__name__)

# FastAPI, Starlette, Pydantic etc...
import fastapi
from fastapi import FastAPI
from fastapi.datastructures import UploadFile
from fastapi.params import File
from fastapi.exceptions import HTTPException
from starlette.responses import RedirectResponse


# Import our components
from app.utils import timed

from app.extractor import UNIVERSAL_EXTRACTOR
from app.models import (
    DefinitionResponse,
    ExtractorRequest,
    ExtractorResponse,
    ImmersiveReaderTokenResponse,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
)

from app.pipeline import PipelineFactoryInstance


# Load environment vars
log.info("Loading .env environment variables ...")
load_dotenv(find_dotenv())
# If running in an (AKS) cluster...
prefix = os.getenv("CLUSTER_ROUTE_PREFIX", "").rstrip("/")


api = FastAPI(
    title="MedJargonBuster API",
    version="v1",
    description="MedJargonBuster is an open-source solution to make medical documents easier to understand for patients, healthcare workers and others. \
        Based on FastAPI, spaCy, Azure Cloud services and best-of-breed open source NLP components and models.",
    openapi_prefix=prefix,
)


@api.get("/", include_in_schema=False)
async def docs_redirect():
    log.info("Redirecting / to openAPI /docs ")
    return RedirectResponse(f"docs")


"""
---
--- Pipeline execution endpoints: Run pipeline on some raw input text. 
--- We can use settings to configure the registered pipeline types (like disabling pipeline steps)
---
"""


@api.post(
    "/pipeline/{name}",
    description="Executes an NLP analysis pipeline with on some input text meta-data and settings. \
    Query params are merged with the settings in the request body and passed to the pipeline. \
    The request body requires either a 'text' value or an 'url'. \
    If an URL is specified, the UniversalExtractor is used to extract the text from that source,\
    before feeding it into the NLP pipeline.",
    tags=["pipeline"],
    response_model=PipelineExecutionResponse,
)
async def execute_pipeline(
    request: fastapi.Request,
    name: str,
    execution_request: PipelineExecutionRequest,
) -> PipelineExecutionResponse:
    """
    Execute a pipeline.
    """

    try:

        # Merge query params into settings object
        settings = execution_request.settings or {}
        settings = {**settings, **dict(request.query_params)}
        log.info(f"Starting pipeline '{name}' with settings: {settings}")

        # Gets the singleton instance of the pipeline
        # As NLP models (more specific: spacy Languages) are expensive to create and apparently stateful,
        # we instantiate every language model only once per process
        pipeline = PipelineFactoryInstance.create(name)

        #
        # settings.clean_only: disable all pipes other than the text preprocessing.
        #
        if settings.get("clean_only"):
            log.info("Running pipeline in 'clean_only' mode...")
            settings = {**settings, **{"enable": ["cleaner"]}}

        # If the pipeline request contains the "url" field, we try to download&extract from that url.
        # Otherwise, we'll use the text in the "text" field of the request json
        if execution_request.url:
            try:
                log.info(f"Starting extration ...")
                url_extract: ExtractorResponse = await extract_from_url(
                    execution_request.url
                )
                raw_text = url_extract.text
                meta = url_extract.meta or {}
            except Exception as e:
                msg = (
                    f"Can't extract text or metadata from url: {execution_request.url}"
                )
                log.error(msg)
                raise HTTPException(400, detail=msg)
        else:
            raw_text = execution_request.text or ""
            meta = execution_request.meta or {}

        # Execute selected pipeline with input text
        #
        # EXECUTE
        #
        response = pipeline.execute(
            text=raw_text,
            meta=meta,
            settings=settings,
        )

        """log.info(
            f"Stats: {create_time_ms}ms model create time, {extract_time_ms}ms text extraction, {execution_time_ms}ms nlp pipeline execution"
        ) """
        return response
    except Exception as e:
        raise HTTPException(500, f"Error executing pipeline '{name}': {str(e)}")


@api.post(
    "/pipeline/{name}/upload",
    response_model=PipelineExecutionResponse,
    description="Run NLP analysis pipeline on an uploaded file \
    see @execute_pipeline for more details",
    tags=["pipeline"],
)
async def execute_pipeline_upload(
    request: fastapi.Request, name: str, file: UploadFile = File(...)
) -> PipelineExecutionResponse:

    # generate settings object from query params
    settings = dict(**request.query_params)

    try:
        # upload file to temp folder and extract the text
        extractResponse = await extract_from_upload(file)

        # Create new pipeline execution request, using extracted input text.
        execution_request = PipelineExecutionRequest(
            text=extractResponse.text, meta=extractResponse.meta, settings=settings
        )

        return await execute_pipeline(
            request=request, name=name, execution_request=execution_request
        )

    except Exception as e:
        log.error(f"Error running pipeline from file upload : {str(e)}")
        raise HTTPException(400, f"Error running pipeline from file upload: {str(e)}")


"""
---
--- Extract endpoints: Extract raw text from file uploads, url links
--- This should support various input file formats like pdf, docx and html
---
"""


@api.post(
    "/extract/upload",
    response_model=ExtractorResponse,
    description="Upload a file and extract raw text + meta-data from it. \
        This uses our UniversalExtractor, which should be capable of extracting text from many different document types,\
            thanks to Apache Tika, Azure Computer Vision OCR, Abbyy Cloud OCR and other best-of-breed extractor components.",
    tags=["extract"],
)
async def extract_from_upload(file: UploadFile = File(...)) -> ExtractorResponse:
    """
    Upload a file and extract text and (possibly) meta-data
    """
    ext = os.path.splitext(file.filename)[1]
    temp = tempfile.NamedTemporaryFile(
        prefix="jargonbuster_", suffix=f"{ext}", delete=False
    )

    # Set the content type
    meta = {"content_type": file.content_type}

    try:
        # Write into temp file
        data = await file.read()
        temp.write(data)

        # Extractor:  parse file into (raw) text
        log.info(
            f"Starting text extraction for '{file.content_type}' from uploaded file '{file.filename}' "
        )
        extractResponse = UNIVERSAL_EXTRACTOR.extract(
            ExtractorRequest(
                filename=temp.name,
                meta=meta,
            )
        )

        return extractResponse

    except Exception as e:
        log.error(str(e))
        raise HTTPException(400, f"Can't extract from the the uploaded file: {str(e)}")
    finally:
        log.debug(f"deleting upload temp file: {temp.name}")
        temp.close()
        os.unlink(temp.name)


@api.get(
    "/extract",
    response_model=ExtractorResponse,
    description="Extract raw text and meta-data from a URL.  \
        This uses our UniversalExtractor, which should be capable of extracting text from many different document types,\
        thanks to Apache Tika, Azure Computer Vision OCR, Abbyy Cloud OCR and other best-of-breed extractor components.",
    tags=["extract"],
)
async def extract_from_url(url: str) -> ExtractorResponse:
    if not url:
        raise HTTPException(400, "Missing 'url' parameter")

    try:
        # UniversalExtractor, pass any url or filename and we'll figure it out :)
        extractResponse = UNIVERSAL_EXTRACTOR.extract(ExtractorRequest(url=url))

        return extractResponse

    except Exception as e:
        log.error(str(e))
        raise Exception(f"Can't extract text from url: {str(e)}")


@api.get(
    "/definition",
    description="Lookup a term in the Merriam-Webster medical dictionary",
    response_model=DefinitionResponse,
)
async def definition(term: str) -> DefinitionResponse:

    apiKey = os.environ.get("MW_API_KEY")

    url = f"https://www.dictionaryapi.com/api/v3/references/medical/json/{term}?key={apiKey}"

    try:

        resp = requests.get(url)
        if resp.ok:
            jsonResp = resp.json()
            if jsonResp:
                definitions = jsonResp
                return DefinitionResponse(term=term, definitions=definitions)
        return DefinitionResponse(term=term, definitions=[])

    except Exception as e:
        log.error(str(e))
        message = f"Error querying dictionary for '{term}'"
        raise HTTPException(930, message)


@api.get(
    "/getIRToken",
    description="Retrieves a client token for integration with the Microsoft Immersive Reader instance.",
    name="getIRToken",
    response_model=ImmersiveReaderTokenResponse,
)
async def getIRToken():
    clientId = str(os.environ.get("AZ_IMMERSIVE_READER_CLIENT_ID"))
    clientSecret = str(os.environ.get("AZ_IMMERSIVE_READER_CLIENT_SECRET"))
    resource = "https://cognitiveservices.azure.com/"
    grantType = "client_credentials"

    # AAD auth endpoint
    tenantId = str(os.environ.get("AZ_IMMERSIVE_READER_TENANT_ID"))
    oauthTokenUrl = f"https://login.windows.net/{tenantId}/oauth2/token"

    subdomain = str(os.environ.get("AZ_IMMERSIVE_READER_SUBDOMAIN"))

    try:
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": clientId,
            "client_secret": clientSecret,
            "resource": resource,
            "grant_type": grantType,
        }

        resp = requests.post(
            oauthTokenUrl,
            data=data,
            headers=headers,
        )
        jsonResp = resp.json()

        if "access_token" not in jsonResp:
            print(jsonResp)
            raise HTTPException(
                910, "AAD Authentication error. Check your IR access credentials"
            )

        token = jsonResp["access_token"]

        return ImmersiveReaderTokenResponse(token=token, subdomain=subdomain)
    except Exception as e:
        message = f"Unable to acquire Azure AD token for Immersive Reader: {str(e)}"
        log.error(message)
        raise HTTPException(920, message)


#
#
# Export the API as v1
#
#
#
API_V1 = api
