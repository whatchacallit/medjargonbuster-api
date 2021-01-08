from app.utils import timed

from os import path
import requests, logging
from urllib3.packages.six import BytesIO


log = logging.getLogger(__name__)


from app.models import ExtractorRequest, ExtractorResponse

# import detector object from tika
from tika import detector


@timed()
def detect_content_type(filename_or_url: str) -> str:
    """
    Use tika to get the content type of a file or url.
    TODO there may be faster/ better ways
    """
    content_type = None
    try:
        if path.isfile(filename_or_url):

            content_type = detector.from_file(filename_or_url)
        else:
            buffer = requests.get(filename_or_url).content
            content_type = detector.from_buffer(BytesIO(buffer))

        log.info(f"Detected '{content_type}' as content type for: {filename_or_url}")

    except Exception as e:
        msg = f"Error detecting content type of '{filename_or_url}' : {str(e)}"
        log.error(msg)
        raise Exception(msg)

    assert content_type

    return content_type


class BaseExtractor(object):
    """
    Extractors can extract raw (e.g. not preprocessed or cleaned) text and metadata from urls and/or local files
    """

    def can_handle(self, request: ExtractorRequest) -> bool:
        raise NotImplementedError("This method should be overriden in subclass")

    def extract(self, request: ExtractorRequest) -> ExtractorResponse:
        raise NotImplementedError("This method should be overriden in subclass")
