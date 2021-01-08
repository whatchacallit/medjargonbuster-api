from datetime import datetime
import uuid
from app.readability import ReadabilityCalculator
import app
from app.cleaner import Cleaner
from app.summarizer import Summarizer
from app.rouge_scorer import RougeScorer
from app.story_generator import StoryGenerator
from app.health_analyzer import HealthAnalyzer

import logging
from spacy.language import Language


log = logging.getLogger(__name__)

import textacy

from app.models import PipelineExecutionResponse
from app.models import PIPELINE_STAGES as STAGE

# Sentencizer
# from pysbd.utils import PySBDFactory# readability score


from app.report_collector import ReportCollector


from app.utils import find_first, timed


class AbstractPipeline(object):
    """
    Abstract base class for Pipelines. This typically just executes & configures  Spacy pipelines,
    with some custom stuff on top.

    """

    name: str = ""
    settings: dict = {}

    def __init__(self, name: str, settings: dict = {}):
        self.name = name
        self.settings = settings

    def create(self) -> Language:
        """
        Create the spaCy nlp pipeline.
        """
        raise NotImplementedError("Please implement this method in your subclass")

    def execute(
        self, text: str, meta: dict = {}, settings: dict = {}
    ) -> PipelineExecutionResponse:
        """
        Executes the previously created spaCy pipeline
        """
        raise NotImplementedError("Please implement this method in your subclass")


class DefaultSummarizerPipeline(AbstractPipeline):

    """
    Default NLP pipeline, using spaCy (https://spacy.io/)
    Default model is  "en_core_web_md" (as we want word vectors) see
    https://spacy.io/models/en#en_core_web_md

    """

    nlp = None

    @timed(save_to="timed", force=True)
    def create(self) -> Language:

        settings = getattr(self, "settings")
        language_model = settings.get("language_model", "en_core_web_md")
        log.info(
            f"Creating new Pipeline for language_model '{language_model}', please wait..."
        )

        # This is an expensive / long running operation
        self.nlp = textacy.load_spacy_lang(
            name=language_model
        )  # spacy.load(language_model)

        # shorthand
        nlp = self.nlp

        #
        # Remove default pipes. We'll re-add them later,
        # but this way the pipeline sequence is more explict and less confusing ;)
        tagger = nlp.remove_pipe(STAGE.TAGGER)[1]
        parser = nlp.remove_pipe(STAGE.PARSER)[1]
        ner = nlp.remove_pipe(STAGE.NER)[1]

        # should be empty now
        assert nlp.pipe_names == []

        #
        # Our pipeline:
        # (see https://spacy.io/usage/processing-pipelines#pipelines for reference)
        #
        #   cleaner -> Cleans the doc (actually, creates a new Doc, so do this first)
        #   tagger -> Assign part-of-speech-tags (Token.pos_ etc.)
        #   sentencizer -> detect sentence boundaries
        #   (sentencizer_scoring -> tries to assess the quality of the sentence splitting by assigning penalities to things that do't look like real sentences)
        #   parser -> dependency parsing
        #   entity_ruler -> mark entities based on (custom) rules
        #   ner -> named entity recognition (based on statistical model)
        #   (x merge_entities -> merge subsequent entities into a single token
        #   (x merge_noun_chunks -> merge subsequent NOUNS into a single token
        #   entity_linker -> disambiguate a named entity in text to a unique knowledge base identifier
        #   summarizer -> do summarization of text
        #   rouge_scorer -> calcuate the ROUGE scores for the summary vs. original (cleaned) text
        #   readability -> calculate readability score
        #   results_collector -> collect all results into usable format for API

        # Cleaner
        cleaner = Cleaner(nlp)
        nlp.add_pipe(cleaner, name=STAGE.CLEANER, first=True)

        # Part-of-speech tagger
        nlp.add_pipe(tagger, name=STAGE.TAGGER)

        # Sentencizer (sets Token.is_sent_start)
        # MUST run before parser
        # sbd_sentencizer = PySBDFactory(nlp, language=language_model[:2])
        # nlp.add_pipe(sbd_sentencizer, name="sentencizer")
        sentencizer = nlp.create_pipe(STAGE.SENTENCIZER)
        nlp.add_pipe(sentencizer, name=STAGE.SENTENCIZER)

        # Sentencizer - quality metrics

        # Parser, creates dependency labels (and Doc.sents)
        nlp.add_pipe(parser, name=STAGE.PARSER)

        # Named Entity recognizer ("ner") - detect named entities (Doc.ents...)
        nlp.add_pipe(ner, name=STAGE.NER)

        # merge entities
        # merge_entities = nlp.create_pipe("merge_entities")
        # nlp.add_pipe(merge_entities, name="merge_entities")

        # Merge noun chunks
        # merge_noun_chunks = nlp.create_pipe("merge_noun_chunks")
        # nlp.add_pipe(merge_noun_chunks, name="merge_noun_chunks")

        # entity linker
        # el = spacy.pipeline.EntityLinker(nlp)
        # nlp.add_pipe(el, name="entity_linker")

        # Extractive Summarization
        summarizer = Summarizer(nlp)
        nlp.add_pipe(summarizer, name=STAGE.SUMMARIZER)

        # ROUGE scorer: "quality" of summary
        rouge_scorer = RougeScorer(nlp)
        nlp.add_pipe(rouge_scorer, name=STAGE.ROUGE_SCORER)

        # Run analyzer, e.g. Text Analytics for health
        analyzer = HealthAnalyzer(nlp)
        nlp.add_pipe(analyzer, name=STAGE.HEALTH_ANALYZER)

        #
        # calculate readability score
        # Our implementation is a wrapper around spacy_readability
        # We calculate Dale-Chall and SMOG scores for the input text and summary (if available)
        readability = ReadabilityCalculator(nlp)
        nlp.add_pipe(readability, name=STAGE.READABILITY)

        #
        # Collects, Aggregates and filters all the results from all previous pipeline stages into
        # something that can be send over as json to an API client.
        #
        # TODO think this over, currently has dependency to all other stages and needs
        # insider knowledge on meta-data and semantics.
        # Fragile, the report collector needs to understand under which conditions
        # what kinda data is (un-)available from previous pipeline stages.

        report = ReportCollector(nlp)
        nlp.add_pipe(report, name=STAGE.REPORT_COLLECTOR)

        # Run story_generator, e.g. generate a readble short story about the document and its topics.
        # maybe (in the future) using GPT-2/3 or paraphraser or something.
        # TODO Key challenge: engaging, simple story covering the key medical entities,
        # concepts while ensuring no semantic distortions from the original text!
        story = StoryGenerator(nlp)
        nlp.add_pipe(story, name=STAGE.STORY_GENERATOR)

        ## TODO think about LUIS/chatbot training data.
        ## Can we train a simple Q&A chatbot on the key topics?
        # ("what's xyz, tell me more about <ENTITY>,
        # who's the author?,
        # is this a credible source?" etc..)
        # hmm... one temporary chatbot per document? or...
        #

        return self.nlp

    @timed(save_to="meta")
    def execute(
        self, text: str, meta: dict = {}, settings: dict = {}
    ) -> PipelineExecutionResponse:
        #
        # run pipeline (expensive )
        #
        pipeline_started = datetime.now()

        # reuse previously constructed pipeline / nlp
        assert self.nlp is not None
        nlp = self.nlp  # a bit shorter

        # apply to input text. If we pass a "disable" list setting, disable those stages from the full pipeline.
        # If we pass an "enable" list as part of the settings, ONLY those stages are executed
        # FIXME turn these known settings keys into Pydantic model/enum/constants, aso available for
        # API docs
        if settings.get("disable"):
            disabled_pipes = settings["disable"]
        elif settings.get("enable"):
            disabled_pipes = [
                str(p) for p in nlp.pipe_names if not str(p) in settings.get("enable")
            ]
        else:
            disabled_pipes = []

        log.info(f"Disabling pipes: {disabled_pipes}")

        with nlp.disable_pipes(disabled_pipes):
            ####
            #
            # Run the pipline !
            #
            ###
            execution_id = uuid.uuid4().hex
            doc = nlp(text)

            # Add basic meta data to report here
            report = {
                "execution_id": execution_id,
                "pipeline": nlp.pipe_names,
                "pipeline_started": pipeline_started.strftime("%Y-%m-%d %H:%M:%S.%f"),
            }

            # Most of the interesting data comes from the report_collector.
            # If you disable (or forgot to "enable") the report_collector in your pipeline execution request
            # you'll only get some very basic meta data back!
            if doc.has_extension(STAGE.REPORT_COLLECTOR):
                report = doc._.get(STAGE.REPORT_COLLECTOR)

            pipeline_finished = datetime.now()
            report["pipeline_finished"] = pipeline_finished.strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )
            report["pipeline_runtime_ms"] = pipeline_finished - pipeline_started

        # merge together: metadata as coming from the extractor + the report with transformed/aggregated values
        # TODO maybe make inclusion of meta data optional here (contains e.g. metadata from extractor)
        result_metadata = {**(meta or {}), **report}

        # "Standardize" some key information, as extractors differ in the meta-data they provide.
        # We'll take the first matching key from a list of aliases, e.g. known extractor-specific fields that may arrive here.
        #
        # - language of the doc
        # - extractor
        # - document type
        # - author(s)
        # - title
        # - pages
        # - ...

        result_metadata["document_language"] = str(
            find_first(meta, ["Language", "language", "lang", "meta_language"])
        )
        result_metadata["document_type"] = str(
            find_first(
                meta,
                [
                    "Content-Type",
                    "content_type",
                    "content-type",
                ],
            )
        )

        result_metadata["document_num_pages"] = int(
            find_first(meta, ["xmpTPg:NPages"], 0)
        )
        result_metadata["document_title"] = str(
            find_first(meta, ["title", "dc:title", "pdf:docinfo:title"])
        )

        return PipelineExecutionResponse(
            text=str(doc.text),
            meta=result_metadata,
        )


class PipelineFactory(object):

    # caching already created pipelines
    # keys are a hash of class names and serialization of settings object
    pipeline_cache = {}

    #
    # define some aliases, so that we can use shorter names for buildin Pipeline classes
    aliases = {
        "default": "DefaultSummarizerPipeline",
        "quick": "DefaultSummarizerPipeline",
    }

    @timed()
    def create(self, name: str = "default", settings: dict = {}) -> AbstractPipeline:
        # lookup class name in shortnames or use as-is
        targetClass = name if not name in self.aliases else self.aliases[name]

        pipelineClass = globals().get(targetClass, None)

        if not pipelineClass:
            raise Exception(f"Pipeline class not found: {name}")
        assert issubclass(pipelineClass, AbstractPipeline)

        pipeline = None
        cache_key = targetClass  # hash(name + json.dumps(settings, sort_keys=True))

        if cache_key in self.pipeline_cache:
            pipeline = self.pipeline_cache[cache_key]
        else:
            pipeline = pipelineClass(type, settings or {})
            pipeline.create()  # this takes a while !
            self.pipeline_cache[cache_key] = pipeline

        return pipeline


PipelineFactoryInstance = PipelineFactory()