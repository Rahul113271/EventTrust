from django.apps import AppConfig


class EventappConfig(AppConfig):
    name = 'EventApp'

    def ready(self):
        try:
            from nltk.corpus import wordnet
            from nltk.stem import WordNetLemmatizer
            wordnet.ensure_loaded()
            WordNetLemmatizer().lemmatize('test')
        except Exception:
            pass
