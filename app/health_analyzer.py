import os
import app
import logging
import requests
from spacy.language import Language
from spacy.tokens import Doc


log = logging.getLogger(__name__)


from app.models import PIPELINE_STAGES as STAGE


class HealthAnalyzer(object):
    """
    Analyzes the document using Azure Text Analytics for health
    """

    nlp: Language = None

    def __init__(self, nlp):
        self.nlp = nlp
        self._endpoint = os.getenv("AZ_TA_FOR_HEALTH_ENDPOINT")

    def __call__(self, doc: Doc):
        if not doc.has_extension(STAGE.HEALTH_ANALYZER) and self._endpoint:
            doc.set_extension(STAGE.HEALTH_ANALYZER, getter=self._analyze_health_text)
        if not self._endpoint:
            log.warning(
                "No endpoint for Azure Text Analytics for health, pls configure env vars ('AZ_TA_FOR_HEALTH_ENDPOINT' etc..)"
            )

        return doc

    def _split_into_documents(
        self, fulltext, language="en", max_doc_length=5120
    ) -> dict:
        """
        Returns ```
        {"documents":
            [{"id":1, "language":"en", "text:"<textchunk-1>"},
             {"id":2, "language":"en", "text:"<textchunk-2>"},
              ...
            ]
        }```
        """
        # Limit of text input StringInfo.LengthInTextElements < 5,120 character, so we might need to split into multiple documents
        # https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/concepts/data-limits?tabs=version-3

        fulltext_chunks = [
            fulltext[i : i + max_doc_length]
            for i in range(0, len(fulltext), max_doc_length)
        ]
        # add the chunks as documents
        documents = {
            "documents": [
                {"language": language, "id": str(i), "text": fulltext_chunks[i]}
                for i in range(0, len(fulltext_chunks))
            ]
        }

        return documents

    #
    #
    def _entitiesByCategory(self, entities, categoryName, offset=0):
        entities = list(filter(lambda d: d["category"] in [categoryName], entities))
        if offset > 0 and len(entities) > 0:
            # Adjust the "offset" of each entity w.r.t. multi-document offset
            for d in entities:
                d.update((k, v + offset) for k, v in d.items() if k == "offset")

        return entities

    def _collect_entities(self, docs, max_doc_length=5120):
        diagnosis = []
        symptoms = []
        treatments = []
        examinations = []

        for i in range(0, len(docs)):
            raw = docs[i]
            offset = i * max_doc_length

            # extract all important entity categories into their own collections
            # adjust text offset (= position of the detected entity within the full text) based on document split
            diagnosis += self._entitiesByCategory(raw["entities"], "Diagnosis", offset)
            symptoms += self._entitiesByCategory(
                raw["entities"], "SymptomOrSign", offset
            )
            treatments += self._entitiesByCategory(
                raw["entities"], "TreatmentName", offset
            )
            examinations += self._entitiesByCategory(
                raw["entities"], "ExaminationName", offset
            )

        result = {
            "diagnosis": diagnosis,
            "symptoms": symptoms,
            "treatments": treatments,
            "examinations": examinations,
        }
        return result

    def _analyze_health_text(self, doc: Doc):
        """
        Getter method. Makes the API call and aggregates the response.
        """

        assert doc.has_extension(STAGE.HEALTH_ANALYZER)
        if not self._endpoint:
            return {}

        headers = (
            {}
        )  # FIXME authorization / API key. Right now this goes to a preview deployment
        # FIXME change to new Azure Web API
        url = f"{self._endpoint}/text/analytics/v3.2-preview.1/entities/health"
        # TODO language
        language = "en"
        try:
            documents = self._split_into_documents(str(doc.text), language)
            response = requests.post(url, headers=headers, json=documents)
            if response.ok:
                docs = response.json()["documents"]
                result = self._collect_entities(docs)
                return result
            else:
                raise Exception(response.reason)

        except Exception as e:
            raise Exception(e)
