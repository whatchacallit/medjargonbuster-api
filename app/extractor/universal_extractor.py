from app.utils import timed
import app
from app.extractor.abbyy_ocr_extractor import AbbyyOcrExtractor
from app.extractor.image_extractor import ImageExtractor
from app.extractor.web_article_extractor import WebArticleExtractor
from app.extractor.wikipedia_extractor import WikipediaExtractor
from app.extractor.tika_extractor import TikaExtractor
from app.extractor.base import BaseExtractor
import logging

log = logging.getLogger(__name__)


from app.models import ExtractorRequest, ExtractorResponse


class UniversalExtractor(BaseExtractor):
    """
    This extractor tries to delegate to specific extractors based on the file/content type discovered.
    """

    tika: BaseExtractor = TikaExtractor()
    wikipedia: BaseExtractor = WikipediaExtractor()
    web_article: BaseExtractor = WebArticleExtractor()
    image_ocr: BaseExtractor = ImageExtractor()
    abbyy_ocr: BaseExtractor = AbbyyOcrExtractor()

    def can_handle(self, request: ExtractorRequest) -> bool:
        return True  # we'll shoot with everything we can...

    @timed(save_to="meta")
    def extract(self, request: ExtractorRequest = None) -> ExtractorResponse:
        result = None
        fallback = False

        try:
            # We should try the most specific extractors first.
            #  Tika is fallback in case no specialized extractor can handle the request,
            # or in case something else goes wrong.
            if self.wikipedia.can_handle(request):
                log.info(f"Extracting text via Wikipedia client: {request.url} ...")
                result = self.wikipedia.extract(request)
            elif self.web_article.can_handle(request):
                log.info(f"Extracting text via newspaper3k client: {request.url} ...")
                result = self.web_article.extract(request)
            elif self.abbyy_ocr.can_handle(request):
                log.info(f"Extracting text via Abbyy Cloud OCR...")
                result = self.abbyy_ocr.extract(request)
            elif self.image_ocr.can_handle(request):
                log.info(
                    f"Extracting text from image via Azure Computer Vision  : {request.url} ..."
                )
                result = self.image_ocr.extract(request)

            else:
                fallback = True
                log.info(
                    f"Extracting text via generic Apache Tika extractor: '{request.url if request.url else request.filename}' ..."
                )
                result = self.tika.extract(request)

        except Exception as e:
            if not fallback:
                log.warn(
                    f"Error using specialized extractor, trying to fall back to tika: {str(e)}"
                )
                fallback = True
                result = self.tika.extract(request)
            else:
                log.error(f"Error using fallback Tika extractor: {str(e)}")

        return result
