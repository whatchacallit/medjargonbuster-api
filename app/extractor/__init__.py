from app.extractor.universal_extractor import UniversalExtractor

from urllib.parse import urljoin
from urllib.request import pathname2url


def filename2url(path: str):
    """
    converts a local filename / path to a file://... url
    """
    return urljoin("file:", pathname2url(path))


# Export universal as (singleton) object
UNIVERSAL_EXTRACTOR = UniversalExtractor()
