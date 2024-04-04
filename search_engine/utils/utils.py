import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string

import streamlit as st

# Download NLTK resources (stopwords)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

def get_tokens(text):
    tokens = word_tokenize(text)

    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    tokens_without_punctuation = [token.translate(translator) for token in tokens]

    # Remove empty strings
    tokens_without_empty = [token for token in tokens_without_punctuation if token.strip()]

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens_without_empty if token.lower() not in stop_words]

    # Lemmatize verbs
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token, pos='v') for token in filtered_tokens]

    # Convert to lowercase
    lowercase_tokens = [token.lower() for token in lemmatized_tokens]

    return lowercase_tokens


if __name__ == "__main__":
    print(get_tokens("Buyback complete, surrendered it back to ford today, goodbye lightning ;("))