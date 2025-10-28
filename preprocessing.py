import re
import unicodedata
from textblob import TextBlob
import ftfy
import logging
import log_utils
from spellchecker import SpellChecker

logger = logging.getLogger("preprocess")

class Preproc:
    def __init__(self, text, candidate_name, interviewer_name):
        self.text = text
        self.candidate_name = candidate_name
        self.interviewer_name = interviewer_name

    # Anonymize Candidate and Interviewer names
    def anonymization(self, text):
        text = re.sub(self.candidate_name, "Candidate", text)
        text = re.sub(self.interviewer_name, "Interviewer", text)
        return text

    # Fix Unicode issues (accents, mojibake) using ftfy and unicodedata
    def normalize_unicode(self, text) -> str:
        text = ftfy.fix_text(text)
        text = unicodedata.normalize("NFC", text)
        return text

    # Basic normalization: whitespace and punctuation
    def clean_text_basic(self, text) -> str:
        text = text.replace("\r", " ").replace("\n", " ")
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s([?.!,:;"])', r'\1', text)
        return text.strip()

    # Correct common grammar/spelling mistakes using TextBlob.
    def correct_text_with_textblob(self, text) -> str:
        corrected_sentences = []
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            blob = TextBlob(sentence)
            corrected_sentences.append(str(blob.correct()))
        return ' '.join(corrected_sentences)

    # Correct spelling using SpellChecker
    def correct_spelling(self, text):
        spell = SpellChecker(language="en")
        words = text.split()
        corrected_words = []
        for word in words:
            if word.lower() in spell:
                corrected_words.append(word)
            else:
                corrected = spell.correction(word)
                corrected_words.append(corrected if corrected else word)
        return ' '.join(corrected_words)

    # Tag dialog segments
    def tag_dialogue_segments(self, text) -> str:
        # Normalize dialogue tags.
        text = re.sub(r'(?i)\b(interview(er)?|question(er)?)\b[:\-]?', "Interviewer:", text)
        text = re.sub(r'(?i)\b(candidate|answer|respond(ent)?)\b[:\-]?', "Candidate:", text)
        text = re.sub(r'\s*([:.])', r'\1', text)
        text = re.sub(r'(Interviewer:|Candidate:)\s*', lambda m: m.group(1) + " ", text)
        return text

    # Full pipeline combining Unicode normalization, correction, and tagging.
    def preprocess_transcript(self) -> str:
        log = "Starting transcript preprocessing..."
        logger.info(log), log_utils.log(log)

        text = self.anonymization(self.text)
        text = self.normalize_unicode(text)
        text = self.clean_text_basic(text)
        text = self.correct_spelling(text)
      #  text = self.correct_text_with_textblob(text)
        text = self.tag_dialogue_segments(text)

        log = "Preprocessing complete."
        logger.info(log),log_utils.log(log)
        return text