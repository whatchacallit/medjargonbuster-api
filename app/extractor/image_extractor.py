import app
from app.extractor.spellcheck import Spellchecker
import os
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


log = logging.getLogger(__name__)


from app.extractor.base import BaseExtractor
from app.models import ExtractorRequest, ExtractorResponse

# Azure custom vision for extracting text from images.
# see: https://github.com/Azure/azure-sdk-for-python
# API docs: https://azuresdkdocs.blob.core.windows.net/$web/python/azure-cognitiveservices-vision-computervision/0.7.0/index.html

# Azure Computer vision quickstart: https://github.com/Azure-Samples/cognitive-services-quickstart-code/blob/master/python/ComputerVision/ComputerVisionQuickstart.py
# https://github.com/Azure-Samples/cognitive-services-python-sdk-samples/blob/master/samples/vision/computer_vision_extract_text.py

from azure.cognitiveservices.vision.computervision import ComputerVisionClient

from azure.cognitiveservices.vision.computervision.models import OcrResult

from msrest.authentication import CognitiveServicesCredentials


region = os.getenv("AZ_COMPUTER_VISION_REGION", None)
key = os.getenv("AZ_COMPUTER_VISION_KEY", None)

from app.extractor.base import detect_content_type


def _is_supported_content_type(filename_or_url: str) -> bool:
    content_type = detect_content_type(filename_or_url)
    return "image" in content_type.lower()


class ImageExtractor(BaseExtractor):
    """
    This does Object Character Recognition (OCR) using Azure Computer Vision Service
    """

    vision_client = None

    def __init__(self):
        try:
            credentials = CognitiveServicesCredentials(key)
            self.vision_client = ComputerVisionClient(
                endpoint="https://" + region + ".api.cognitive.microsoft.com/",
                credentials=credentials,
            )
        except Exception as e:
            log.warning(
                f"Can't init Azure ComputerVisionClient (make sure env vars are correct): {str(e)}"
            )
            self.vision_client = None

    def _extract_text_from_image(self, filename_or_url: str, language: str = "en"):
        # url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Broadway_and_Times_Square_by_night.jpg/450px-Broadway_and_Times_Square_by_night.jpg"
        # API docs: https://azuresdkdocs.blob.core.windows.net/$web/python/azure-cognitiveservices-vision-computervision/0.7.0/azure.cognitiveservices.vision.computervision.models.html#azure.cognitiveservices.vision.computervision.models.OcrResult

        # Raw response from Azure Cognitive Service
        ocr_result: OcrResult = None

        if os.path.isfile(filename_or_url):
            # Process a local file
            local_image = open(filename_or_url, "rb")
            ocr_result = self.vision_client.recognize_printed_text_in_stream(
                local_image, detect_orientation=True, language="unk"
            )
        else:
            # Process a public URL
            ocr_result = self.vision_client.recognize_printed_text(
                url=filename_or_url, detect_orientation=True, language="unk"
            )

        # Transfer all data into meta

        meta = {
            "language": ocr_result.language,
            "text_angle": ocr_result.text_angle,
            "orientation": ocr_result.orientation,
        }

        # TODO improve word list w. medical dictionary + more languages.
        # FIXME: not very good results right now
        spellcheck = Spellchecker(language=ocr_result.language)

        # Now extract the text from all regions
        fulltext = ""
        for region in ocr_result.regions:
            # print("Bounding box: {}".format(region.bounding_box))
            for line in region.lines:
                # print("Bounding box: {}".format(line.bounding_box))
                for word in line.words:
                    corrected = spellcheck.correct_word(word.text)
                    if corrected != word.text:
                        log.debug(f"auto-corrected word: {word.text} -> {corrected}")
                    fulltext += corrected + " "
                fulltext += "\n"
            fulltext += "\n\n"

        # Return mutiple values
        return fulltext, meta

    def can_handle(self, request: ExtractorRequest) -> bool:
        if not self.vision_client:
            log.warn(
                "Can't handle input, as the Azure Computer Vision Client hasn't been initialized"
            )
            return False

        return (request.url and _is_supported_content_type(request.url)) or (
            request.filename and _is_supported_content_type(request.filename)
        )

    def extract(self, request: ExtractorRequest) -> ExtractorResponse:
        log.info(f"Extracting text from image (Azure Computer Vision OCR) ...")

        try:
            if request.url:
                fulltext, meta = self._extract_text_from_image(request.url)
            else:
                fulltext, meta = self._extract_text_from_image(request.filename)
            # TODO get some meta data as well
            meta = {**meta, **{"source": "image", "extractor": "az-vision"}}

            return ExtractorResponse(text=fulltext, meta=meta)
        except Exception as e:
            msg = f"Error extracting text using Azure Computer Vision: '{str(e)}'"
            log.error(msg)
            return ExtractorResponse(error=msg)
