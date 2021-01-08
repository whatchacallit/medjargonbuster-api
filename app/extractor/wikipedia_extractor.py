from app.extractor.base import BaseExtractor
import app

import logging


log = logging.getLogger(__name__)

from app.models import ExtractorRequest, ExtractorResponse

# wikipedia client
from wikipedia import wikipedia


class WikipediaExtractor(BaseExtractor):
    """
    Extractor using dedicated library to extract content from Wikipedia pages.
    The ExtractorRequest.url is expected to point to a wikipedia.org page,
    like https://en.wikipedia.org/wiki/Patellar_dislocation

    Using https://github.com/goldsmith/Wikipedia
    """

    def can_handle(self, request: ExtractorRequest) -> bool:
        # we handle only direct wikipedia page URLs (no local filenames, no searches etc.)
        return request.url and "wikipedia.org/wiki" in str(request.url).lower()

    def extract(self, request: ExtractorRequest) -> ExtractorResponse:
        try:
            # last url path segment should be our page name, e.g. "Patellar_dislocation"
            page_name = request.url.split("/")[-1]

            page = wikipedia.page(page_name)
            text = page.content
            meta = {
                "source": "wikipedia",
                "source_url": page.url,
                "title": page.title,
                "summary": page.summary,
                "images": page.images,
                "references": page.references,
            }
            # construct response
            response_meta = {**(request.meta or {}), **meta}
            response = ExtractorResponse(meta=response_meta, text=text or "")
        except Exception as e:
            msg = f"Error using wikipedia extractor: {str(e)}"
            log.error(msg)
            response = ExtractorResponse(error=msg)

        return response
