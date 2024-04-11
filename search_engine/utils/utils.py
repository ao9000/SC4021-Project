import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
import re
from collections import Counter
import streamlit as st

# Check if NLTK resources are already downloaded
def check_nltk_resources():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        return True
    except LookupError:
        return False
    

# Download NLTK resources if not already downloaded
if not check_nltk_resources():
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
else:
    print("NLTK resources are already downloaded.")


def get_tokens_freq_dict(text, return_type='dictionary'):
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

    if return_type == "dictionary":
        word_freq = Counter(lowercase_tokens)
        return word_freq
    else:
        return lowercase_tokens

def bold_matching_words(query, text, color="DodgerBlue"):
    # Split the query into individual words
    query_words = query.split()
    
    # Escape special characters in each word of the query
    escaped_query_words = [re.escape(word) for word in query_words]
    
    # Create regex patterns for each word in the query
    patterns = [re.compile(r'\b(' + word + r')\b', re.IGNORECASE) for word in escaped_query_words]
    
    # Replace matching words in the text with the same word wrapped in '**'
    bold_text = text
    for pattern in patterns:
        bold_text = pattern.sub(r'<strong style="color: ' + color + r';">\1</strong>', bold_text)
    
    return bold_text


def format_text(text):
    # Format italic words enclosed in *<words>*
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Format bold words enclosed in **<words>**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Underline words enclosed in square brackets [words]
    text = re.sub(r'\[([^\]]+)\]', r'<u>\1</u>', text)
    
    return text

def get_text_html_color(text):
    if text == "positive":
        return "YellowGreen"
    elif text == "neutral":
        return "SteelBlue"
    elif text == "negative":
        return "Tomato"
    elif text == "objective":
        return "Indigo"
    else: #elif text == "subjective":
        return "DarkOrange"
    
def update_tokens_and_labels(doc):

    if doc['vader_sentiment'][0] == 'positive':
        st.session_state["tokens"]["vader_positive"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["vader_positive"] += 1

    elif doc['vader_sentiment'][0] == 'neutral':
        st.session_state["tokens"]["vader_neutral"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["vader_neutral"] += 1

    else: # if doc['vader_sentiment'][0] == 'negative':
        st.session_state["tokens"]["vader_negative"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["vader_negative"] += 1

    if doc['vader_subjectivity'][0] == 'subjective':
        st.session_state["tokens"]["vader_subjective"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["vader_subjective"] += 1
    
    else:
        st.session_state["tokens"]["vader_objective"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["vader_objective"] += 1

    ###############################################

    if doc['textblob_sentiment'][0] == 'positive':
        st.session_state["tokens"]["textblob_positive"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["textblob_positive"] += 1

    elif doc['textblob_sentiment'][0] == 'neutral':
        st.session_state["tokens"]["textblob_neutral"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["textblob_neutral"] += 1

    else: # if doc['vader_sentiment'][0] == 'negative':
        st.session_state["tokens"]["textblob_negative"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["textblob_negative"] += 1

    if doc['textblob_subjectivity'][0] == 'subjective':
        st.session_state["tokens"]["textblob_subjective"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["textblob_subjective"] += 1
    
    else:
        st.session_state["tokens"]["textblob_objective"].update(get_tokens_freq_dict(doc["text"][0]))
        st.session_state["label_count"]["textblob_objective"] += 1
        

if __name__ == "__main__":
    # Example usage
    query = "have"
    text = "I have a few words and I have another string that may have the words in query."
    bold_text = bold_matching_words(query, text)
