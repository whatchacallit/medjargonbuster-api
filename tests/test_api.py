from datetime import datetime
import os
import sys
from timeit import default_timer as timer
import json
from urllib.parse import urlencode

from app.models import (
    ExtractorRequest,
    ExtractorResponse,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
)
from app.extractor.tika_extractor import TikaExtractor


from fastapi.testclient import TestClient

from app import API_V2

from app.pipeline import PipelineFactory, PipelineFactoryInstance
from starlette.datastructures import URL


root_path = "/api/v2"
client = TestClient(API_V2)

# path to test documents
TEST_DOCS = f"{os.path.dirname(__file__)}/../test-documents"
REPORT_PATH = f"{os.path.dirname(__file__)}/../test-reports"

DOCUMENTS = {
    # a typical medical research paper
    "simple.pdf": f"{TEST_DOCS}/research_papers/simple.pdf",
    # a well structured research paper, but from a different domain (NLP, abstractive summarization)
    "summarization.pdf": f"{TEST_DOCS}/research_papers/summarization.pdf",
    # Guideline for breast cancer patients
    "breast_cancer_report.pdf": f"{TEST_DOCS}/guides/Breastcancerorg_Pathology_Report_Guide_2016.pdf",
    # anonymized medical surgery report (in german)
    "de_report.docx": f"{TEST_DOCS}/clinical_reports/de-report01.docx",
    # A scanned and anonymized medical report, in german. No extractable text, needs OCR pre-processing
    "de_report_scanned.pdf": f"{TEST_DOCS}/clinical_reports/de-OP-Bericht-001.pdf",
    # A local image file with a scanned report as image
    "de_report_scanned.jpeg": f"{TEST_DOCS}/clinical_reports/de-OP-Bericht-001.jpeg",
    # URL: wikipedia article
    "wikipedia_breast_cancer.html": URL("https://en.wikipedia.org/wiki/Breast_cancer"),
    # URL: some health related web news article
    "web_article_diet_plan_summary.html": URL(
        "https://www.breastcancer.org/research-news/diet-for-diabetes-risk-means-better-survival"
    ),
}


def _extractTestDocument(filename) -> ExtractorResponse:
    request = ExtractorRequest(filename=filename)
    response = TikaExtractor().extract(request)
    assert not response.error, response.error

    return response


def _extractUrlDocument(url) -> ExtractorResponse:
    request = ExtractorRequest(url=url)
    response = TikaExtractor().extract(request)
    assert not response.error, response.error

    return response


def test_index():
    response = client.get("/")
    assert response.status_code == 200


def test_default_pipeline():
    # Just get the raw text
    text = _extractTestDocument(DOCUMENTS["simple.pdf"]).text
    data = PipelineExecutionRequest(text=text).json()

    response = client.post("/pipeline/default", data)
    assert response.status_code == 200


def test_extract_and_clean():
    files_to_upload = {
        "file": open(
            DOCUMENTS["simple.pdf"],
            "rb",
        )
    }

    response: PipelineExecutionResponse = client.post(
        "/pipeline/default/upload?clean_only=true",
        files=files_to_upload,
    )
    assert response.status_code == 200

    resp = response.json()
    print(resp)
    assert len(resp["text"]) > 0

    pipeline_names = resp.get("meta", {}).get("pipeline")

    assert ["cleaner"] == pipeline_names


def test_default_pipeline_upload():
    files_to_upload = {
        "file": open(
            DOCUMENTS["simple.pdf"],
            "rb",
        )
    }
    response: PipelineExecutionResponse = client.post(
        "/pipeline/default/upload", files=files_to_upload
    )

    resp = response.json()
    print(json.dumps(resp, indent=1))

    print(
        f"Timing for 'simple.pdf' on 'default' pipeline (excl. upload) : {resp['meta']['pipeline_runtime_ms']} ms"
    )

    assert response.status_code == 200


def test_scanned_text_from_url():
    # FIXME find adequate example report as scanned image (.png, .jpeg, ...)
    # url = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-sample-data-files/master/ComputerVision/Images/printed_text.jpg"
    url = "http://image.slidesharecdn.com/breastcancerwrittenreport-140216213801-phpapp02/95/breast-cancer-written-report-19-638.jpg"
    response: PipelineExecutionResponse = None

    response = client.post("/pipeline/default", json={"url": url})

    assert response.status_code == 200
    data = response.json()

    assert len(data["text"]) > 0
    assert data["meta"]["source"].lower() == "image"


def test_from_url():

    # Test URL from Wikipedia
    url = f"https://en.wikipedia.org/wiki/Breast_cancer"
    response: PipelineExecutionResponse = client.post(
        "/pipeline/default", json={"url": url}
    )
    assert response.status_code == 200

    data = response.json()
    meta = data["meta"]
    text = data["text"]
    assert meta["source"] == "wikipedia"
    assert len(text) > 0
    assert meta["title"].lower() == "breast cancer"

    # Test URL for NYT article
    url = f"https://www.nytimes.com/2020/12/28/health/covid-psychosis-mental.html"
    response = client.post("/pipeline/default", json={"url": url})
    assert response.status_code == 200
    data = response.json()
    text = data["text"]
    meta = data["meta"]
    assert meta["source"] == "web_article"
    assert (
        meta["title"].lower()
        == "small number of covid patients develop severe psychotic symptoms"
    )
    assert len(text) > 0

    # Now try a (hosted) pdf research paper
    url = "https://www.cgi.com/sites/default/files/white-papers/cgi-health-challenges-white-paper.pdf"
    response = client.post("/pipeline/default", json={"url": url})
    assert response.status_code == 200
    data = response.json()
    text = data["text"]
    assert len(text) > 0
    meta = data["meta"]
    assert meta["source"] == "document"
    assert meta["Content-Type"] == "application/pdf"
    assert meta["dc:language"] == "en-US"
    assert meta["pdf:encrypted"] == "false"
    assert meta["title"] == "Healthcare Challenges and Trends"

    response = client.post(
        "/pipeline/default", json={"url": "http://www.oecd.org/sti/inno/37450246.pdf"}
    )
    assert response.status_code == 200

    # TODO: Test for error messages for inaccessible urls:
    # requiring auth, 404 errors, encrypted/protected pdfs etc..


def test_log_test_documents():
    for name, path in DOCUMENTS.items():
        try:
            if isinstance(path, URL):
                extract_response = _extractUrlDocument(str(path))
            else:
                extract_response = _extractTestDocument(str(path))

            text = extract_response.text
            meta = extract_response.meta

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            raw_file = open(f"{REPORT_PATH}/{name}-raw.txt", "w+", encoding="UTF-8")
            raw_file.write(text)
            raw_file.close()

            pipeline = PipelineFactoryInstance.create(name="default", settings={})
            result = pipeline.execute(text=text or "", meta=meta or {})
            assert result.meta
            assert result.meta.get("summary_sentences")

            # work with returned meta data
            meta = result.meta

            processed_file = open(
                f"{REPORT_PATH}/{name}-processed.txt", "w+", encoding="UTF-8"
            )
            processed_file.write(result.text)
            processed_file.close()

            result_file = open(
                f"{REPORT_PATH}/{name}-summary-log.txt", "a", encoding="UTF-8"
            )

            result_file.write("==========================================\n")
            result_file.write(f"Created: {timestamp}\n")
            result_file.write(f"\n- ")  # marks beginning of summary
            result_file.write("\n- ".join(meta["summary_sentences"]))
            result_file.write(f"\n\n")

            result_file.close()
        except Exception as e:
            print(f"Error generating test reports: {str(e)}")
            raise Exception(e)
