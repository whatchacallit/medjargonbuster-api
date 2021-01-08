import app
import time
from app.extractor.base import BaseExtractor
import os, os.path, logging, requests, tempfile
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from requests_file import FileAdapter
from urllib3.packages.six import BytesIO, StringIO


log = logging.getLogger(__name__)


from app.models import ExtractorRequest, ExtractorResponse


from app.extractor.base import detect_content_type

# Alternative: use ABBYY OCR service (commercial)
# This extractor uses Abbyy OCR service to extract text from (scanned/ photographed) images.
# It is a third party cloud service with its own license agreement and terms. Costs (e.g. per processed page) will occur.
# More info:
# https://www.abbyy.com/cloud-ocr-sdk/
# https://github.com/abbyy/ocrsdk.com
# We'll use the V2 json API (preview), see:
# https://support.abbyy.com/hc/en-us/sections/360004931659-API-v2-JSON-version-

abbyy_ocr_app_id = os.getenv("ABBYY_OCR_APP_ID", None)
abbyy_ocr_password = os.getenv("ABBYY_OCR_PASSWORD", None)
abbyy_ocr_url = os.getenv("ABBYY_OCR_URL", None)


def _is_supported_content_type(filename_or_url: str) -> bool:
    content_type = detect_content_type(filename_or_url)

    return "image" in content_type.lower()


class AbbyyOcrExtractor(BaseExtractor):
    def _processImage(self, filename):
        # see: https://support.abbyy.com/hc/en-us/articles/360017269680-processImage-Method
        url = f"{abbyy_ocr_url}/v2/processImage?language=english,german&profile=textExtraction&exportformat=txt"
        try:
            with open(filename, "rb") as image_file:
                data = image_file.read()
                result = requests.post(
                    url, auth=(abbyy_ocr_app_id, abbyy_ocr_password), data=data
                )
                if result.status_code == 200:
                    taskId = result.json()["taskId"]
                    result_url = f"{abbyy_ocr_url}/v2/getTaskStatus?taskId={taskId}"
                    downloadUrl = None
                    while not downloadUrl:
                        # FIXME: add timeout / error handling
                        time.sleep(1)
                        result = requests.get(
                            result_url, auth=(abbyy_ocr_app_id, abbyy_ocr_password)
                        )
                        urls = result.json().get("resultUrls", None)
                        if urls:
                            downloadUrl = urls[0]

                    return requests.get(downloadUrl).text
                return None

        except Exception as e:
            log.error(e)

    def can_handle(self, request: ExtractorRequest) -> bool:
        if not abbyy_ocr_app_id:
            log.warning(
                "No ABBYY OCR application id set via 'ABBYY_OCR_APP_ID' env var, I'm out..."
            )
            return False

        # check if the env vars are set and the filename/url points to a supported file format (image or pdf)
        is_supported_format = False

        # URL -> try a HEAD request to determine the MIME content type
        if request.url:
            is_supported_format = _is_supported_content_type(request.url)
        elif request.filename:
            # filename -> check for file extension for image file
            extension = os.path.splitext(request.filename)[1][1:].lower()
            is_supported_format = extension in [
                "jpg",
                "jpeg",
                "bmp",
                "tiff",
                "png",
                "gif",
            ]

        return is_supported_format

    def extract(self, request: ExtractorRequest) -> ExtractorResponse:
        log.info(f"Extracting text from image (Abbyy Cloud OCR) ...")

        tmp = None

        try:
            # if url, download to temp file first
            if request.url:
                r = requests.get(request.url)
                tmp = tempfile.NamedTemporaryFile(delete=False, mode="wb")
                tmp.write(r.content)
                tmp.close()
                fulltext = self._processImage(tmp.name)
            else:
                fulltext = self._processImage(request.filename)
            meta = {**request.meta, **{"source": "image", "extractor": "abbyy_ocr"}}
            return ExtractorResponse(text=fulltext or "", meta=meta)
        except Exception as e:
            msg = f"Error extracting text using Abbyy Cloud OCR: '{str(e)}'"
            log.error(msg)
            return ExtractorResponse(error=msg)
        finally:
            if tmp:
                tmp.close()
                os.unlink(tmp.name)
