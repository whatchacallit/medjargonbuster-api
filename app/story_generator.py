import app
import logging
import os
from spacy.language import Language
from spacy.tokens import Doc

# import gpt_2_simple as gpt2


log = logging.getLogger(__name__)

from app.models import PIPELINE_STAGES as STAGE


class StoryGenerator(object):
    """
    generates some human-readable "story" from our NLP analysis, preserving meaming and key points.
    work in progress: may use something like GPT-2, paraphrasing or manual "templating"
    """

    name = STAGE.STORY_GENERATOR
    nlp: Language = None
    # Which model to use. 124M = 500 MB !
    # gpt2_model_name: str = "124M"

    def __init__(self, nlp):
        self.nlp = nlp

    """     if not os.path.isdir(os.path.join("models", self.gpt2_model_name)):
            log.info(f"Downloading {self.gpt2_model_name} model...")
            gpt2.download_gpt2(model_name=self.gpt2_model_name)
            # model is saved into current directory under /models/124M/ """

    def __call__(self, doc):
        if not doc.has_extension(STAGE.STORY_GENERATOR):
            doc.set_extension(STAGE.STORY_GENERATOR, getter=self._generate_story)

        return doc

    def _generate_story(self, doc):
        single_text = (
            "Generate a story talking about key concepts, results, summary and ..."
        )

        """ sess = gpt2.start_tf_sess()
        gpt2.load_gpt2(sess, model_name=self.gpt2_model_name)

        # gpt2.finetune(sess,
        #      file_name,
        #      model_name=self.gpt2_model_name,
        #      steps=1000)   # steps is max number of training steps
        single_text = gpt2.generate(
            sess, model_name=self.gpt2_model_name, return_as_list=True
        )[0]
         """

        return single_text
