import app
from app.extractor.base import BaseExtractor
from app.models import ExtractorRequest, ExtractorResponse
import logging
from urllib3.packages.six import BytesIO
import requests

# import parser and detector object from tika
from tika import parser


log = logging.getLogger(__name__)


class TikaExtractor(BaseExtractor):
    """
    Apache Tika (https://tika.apache.org/) is a text/content extraction tool that supports A LOT of different
    document types.
    TODO run as separate service and do
    tika.TikaClientOnly = True

    Python wrapper: https://github.com/chrismattmann/tika-python
    """

    def can_handle(self, request: ExtractorRequest):
        return True  # Tika is our fallback extractor - should support most cases

    def extract(self, request: ExtractorRequest = None) -> ExtractorResponse:
        try:
            # request options to the document url and the tika server where we send the bytes to
            # see: https://requests.kennethreitz.org/en/master/api/#requests.request
            tika_req_options = {"timeout": 15}
            document_req_options = {"timeout": 15, "allow_redirects": True}

            if request.url:
                resp = requests.get(request.url, **document_req_options)

                buffer = BytesIO(resp.content)
                parsed = parser.from_buffer(buffer, requestOptions=tika_req_options)
            else:
                parsed = parser.from_file(
                    request.filename, requestOptions=tika_req_options
                )

            text = parsed["content"] or ""
            # merge parsed metadata with source info
            meta = {**parsed["metadata"], **{"source": "document"}}

            # construct response
            response = ExtractorResponse(meta=meta, text=text)
        except Exception as e:
            msg = f"Error extracting text via Tika extractor: '{str(e)}'"
            log.error(msg)
            response = ExtractorResponse(error=msg)

        return response
