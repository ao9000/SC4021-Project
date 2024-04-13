import streamlit as st
import datetime
import matplotlib.pyplot as plt

from annotated_text import annotated_text
from wordcloud import WordCloud
from collections import Counter

from utils.utils import bold_matching_words, format_text, get_text_html_color, get_tokens_freq_dict, update_tokens_and_labels

def init_session_states():
    if "query" not in st.session_state:
        st.session_state["query"] = None

    if "search_suggested" not in st.session_state:
        st.session_state["search_suggested"] = False

    if "suggested_query" not in st.session_state:
        st.session_state["suggested_query"] = None

    if "results" not in st.session_state:
        st.session_state["results"] = None

    if "additional_options" not in st.session_state:
        st.session_state["additional_options"] = None

    if "tokens" not in st.session_state:
        st.session_state["tokens"] = {
            "vader_positive": Counter(),
            "vader_neutral": Counter(),
            "vader_negative": Counter(),
            "vader_subjective": Counter(),
            "vader_objective": Counter(),
            "textblob_positive": Counter(),
            "textblob_neutral": Counter(),
            "textblob_negative": Counter(),
            "textblob_subjective": Counter(),
            "textblob_objective": Counter()
        }

    if "label_count" not in st.session_state:
        st.session_state["label_count"] = {
            "vader_positive": 0,
            "vader_neutral": 0,
            "vader_negative": 0,
            "vader_subjective": 0,
            "vader_objective": 0,
            "textblob_positive": 0,
            "textblob_neutral": 0,
            "textblob_negative": 0,
            "textblob_subjective": 0,
            "textblob_objective": 0
        }

    if "query_time" not in st.session_state:
        st.session_state["query_time"] = None 

def suggest_diff_query(solr_manager, query):
    if not len(st.session_state["query"].split(' ')) > 1:
        suggested_query = solr_manager.spellcheck(query)["spellcheck"]["suggestions"]
        # No spell suggestions
        if len(suggested_query) == 0:
            return None
        else:
            suggested_query = suggested_query[1]["suggestion"][0]["word"]
            return suggested_query
        
    else:
        return None

def suggest_spell_correction(button_id):
    _, message_col, _= st.columns([1,5,1])
    with message_col:
        st.write(f"Did you mean: **{st.session_state['suggested_query']}**?")

        if st.button(f"Search with **{st.session_state['suggested_query']}** instead", key=button_id):
            st.session_state["search_suggested"] = True
            st.rerun()

def get_results(solr_manager, tokens_init_format, label_init_format):

    st.session_state["tokens"] = tokens_init_format
    st.session_state["label_count"] = label_init_format

    if st.session_state["additional_options"]["retrieve_type"] == "Posts and Comments (Will take a longer time)":
        result_type = 'post'
    elif st.session_state["additional_options"]["retrieve_type"] == "Posts only":
        result_type = 'post'
    else:
        result_type = 'comment'

    st.write('---')

    tmp_date_start = st.session_state["additional_options"]["date_start"]
    tmp_date_end = st.session_state["additional_options"]["date_end"]

    # Date range for querying
    min_date = datetime.date(2016, 12, 19) # min date in csv
    max_date = datetime.date(2024, 3, 22) # max date in csv

    if tmp_date_start and tmp_date_end:
        tmp_date_range = [str(tmp_date_start.strftime('%Y-%m-%d')), str(tmp_date_end.strftime('%Y-%m-%d'))]
    elif tmp_date_start and not tmp_date_end:
        tmp_date_range = [str(tmp_date_start.strftime('%Y-%m-%d')), str(max_date.strftime('%Y-%m-%d'))]
    elif not tmp_date_start and tmp_date_end:
        tmp_date_range = [str(min_date.strftime('%Y-%m-%d')), str(tmp_date_end.strftime('%Y-%m-%d'))]
    else:
        tmp_date_range = None

    if st.session_state["additional_options"]["exact_matching"]:
        results = solr_manager.get_text_query_result(st.session_state["query"], result_type, tmp_date_range, phrase_search=True, num_rows=st.session_state["additional_options"]["retrieve_num"])
    else:
        results = solr_manager.get_text_query_result(st.session_state["query"], result_type, tmp_date_range, num_rows=st.session_state["additional_options"]["retrieve_num"])

    if results["response"]["numFound"] < st.session_state["additional_options"]["retrieve_num"]:
        st.session_state["suggested_query"] = suggest_diff_query(solr_manager, st.session_state["query"])
    else:
        st.session_state["suggested_query"] = None

    if results["response"]["numFound"] == 0 and not st.session_state["suggested_query"]:
        st.session_state["results"] = {"post": [], "comment": []}

    elif results["response"]["numFound"] == 0 and st.session_state["suggested_query"]:
        st.session_state["results"] = {"post": [], "comment": []}

    else:

        if st.session_state["additional_options"]["retrieve_type"] == "Posts and Comments (Will take a longer time)":
            comment_list = []
            for doc in results["response"]["docs"]:
                update_tokens_and_labels(doc)

                tmp_comment_list = solr_manager.get_comment_from_post_id_and_text(doc["id"], st.session_state["query"])
                if tmp_comment_list:
                    for comment in tmp_comment_list:
                        update_tokens_and_labels(comment)
                    comment_list.append(tmp_comment_list)
                
                    

            st.session_state["results"] = {"post": results["response"]["docs"], "comment": comment_list}

        else:
            if result_type == 'post':
                st.session_state["results"] = {"post": results["response"]["docs"], "comment": []}
            else:
                st.session_state["results"] = {"post": [], "comment": results["response"]["docs"]}

            for doc in results["response"]["docs"]:
                update_tokens_and_labels(doc)

def display_analysis(model_selection, label_category):
    if model_selection == "VADER":
        tmp_prefix = "vader"
    else:
        tmp_prefix = "textblob"
    
    if label_category == "Positive Mood" or label_category == "Neutral Mood" or label_category == "Negative Mood":
        # Extract values for vader_positive, vader_negative, and vader_neutral
        selected_data = {key: st.session_state["label_count"][key] for key in [f'{tmp_prefix}_positive', f'{tmp_prefix}_negative', f'{tmp_prefix}_neutral']}
        # Explode settings
        explode = [0, 0, 0] 
        # For wordcloud
        filter_category = f'{tmp_prefix}_sentiment'
    else:
        # Extract values for vader_subjective, vader_objective
        selected_data = {key: st.session_state["label_count"][key] for key in [f'{tmp_prefix}_subjective', f'{tmp_prefix}_objective']}
        # Explode settings
        explode = [0, 0]
        # For wordcloud
        filter_category = f'{tmp_prefix}_subjectivity'

    print()
    print("selected_data:")
    print(selected_data)
    print()

    # Calculate total sum of values
    total = sum(selected_data.values())
    # Normalize values and convert to percentages
    normalized_values = [value / total * 100 for value in selected_data.values()]

    labels=list(selected_data.keys())

    if label_category == 'Positive Mood':
        explode[labels.index(f'{tmp_prefix}_positive')] = 0.2 
    elif label_category == 'Neutral Mood':
        explode[labels.index(f'{tmp_prefix}_neutral')] = 0.2 
    elif label_category == 'Negative Mood':
        explode[labels.index(f'{tmp_prefix}_negative')] = 0.2 
    elif label_category == 'Subjective':
        explode[labels.index(f'{tmp_prefix}_subjective')] = 0.2
    else:
        explode[labels.index(f'{tmp_prefix}_objective')] = 0.2

    # Modify labels by removing prefix and capitalizing them, and include percentage numbers
    labels = [f"{x.replace(tmp_prefix+'_', '').capitalize()} ({normalized_values[i]:.1f}%)" for i, x in enumerate(labels)]

    pie_col, _, cloud_col = st.columns([2,0.3,2])
    with pie_col:
        # Plot the pie chart
        fig, ax = plt.subplots()
        ax.pie(normalized_values, labels=labels, explode=explode, startangle=90, labeldistance=1.15)
        ax.legend(loc='upper right', bbox_to_anchor=(-0.2, 1))
        ax.set_title(f"Percentage of Category according to {tmp_prefix.capitalize()} model")
        st.pyplot(fig)
    with cloud_col:
        if label_category == 'Positive Mood':
            word_freq_dict = dict(st.session_state['tokens'][f'{tmp_prefix}_positive'])
            filter_value = 'positive'
        elif label_category == 'Neutral Mood':
            word_freq_dict = dict(st.session_state['tokens'][f'{tmp_prefix}_neutral'])
            filter_value = 'neutral'
        elif label_category == 'Negative Mood':
            word_freq_dict = dict(st.session_state['tokens'][f'{tmp_prefix}_negative'])
            filter_value = 'negative'
        elif label_category == 'Subjective':
            word_freq_dict = dict(st.session_state['tokens'][f'{tmp_prefix}_subjective'])
            filter_value = 'subjective'
        else:
            word_freq_dict = dict(st.session_state['tokens'][f'{tmp_prefix}_objective'])
            filter_value = 'objective'

        if not len(word_freq_dict) > 0:
            st.info("No WordCloud is displayed because there is no results for the current model and analysis setting.")
        else:
            display_wordcloud(word_freq_dict, label_category, model_selection)

    st.write('---')

    display_single_only(analysis_mode=True, filter_category=filter_category, filter_value=filter_value)

def display_mood_subjectivity(doc, title_font_size, content_font_size):

    st.markdown(f"<p style='text-align: center;font-size:{title_font_size}px;'><strong>Text Analysis:</strong></p>", unsafe_allow_html=True,
                help="VADER and TextBlob are AI tools that help us understand the 'mood' and subjectivity of the text.\
                    If they give different categories, it's not a matter of one being right and the other wrong. \
                    Instead, it's like getting two perspectives on the same text. \
                    You can consider both and see which resonates more with your understanding of the text. \
                    Remember, these tools are here to help you, but your interpretation matters the most!")
            
    vader_col, textblob_col = st.columns([1,1])
    with vader_col:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;font-size:{title_font_size}px;'><strong>VADER model:</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;font-size:{content_font_size}px;'>Mood: <strong style='color:{get_text_html_color(doc['vader_sentiment'][0])}';'>\
                        {doc['vader_sentiment'][0].capitalize()}</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;font-size:{content_font_size}px;'>Subjectivity: <strong style='color:{get_text_html_color(doc['vader_subjectivity'][0])}';'>\
                        {doc['vader_subjectivity'][0].capitalize()}</strong></p>", unsafe_allow_html=True)
            
    with textblob_col:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;font-size:{title_font_size}px;'><strong>TextBlob model:</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;font-size:{content_font_size}px;'>Mood: <strong style='color:{get_text_html_color(doc['textblob_sentiment'][0])}';'>\
                        {doc['textblob_sentiment'][0].capitalize()}</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;font-size:{content_font_size}px;'>Subjectivity: <strong style='color:{get_text_html_color(doc['textblob_subjectivity'][0])}';'>\
                        {doc['textblob_subjectivity'][0].capitalize()}</strong></p>", unsafe_allow_html=True)

def display_single_only(analysis_mode=False, filter_category=None, filter_value=None):

    _, col, _= st.columns([1,5,1])

    if analysis_mode:
        result_type = "Text"

        if len(st.session_state["results"]["comment"]) > 0:
            if type(st.session_state["results"]["comment"][0]) is list: # if list of list
                doc_list = st.session_state["results"]["post"] + [item for sublist in st.session_state["results"]["comment"] for item in sublist]
            else: # if dictionary
                doc_list = st.session_state["results"]["post"] + st.session_state["results"]["comment"]
        else:
            doc_list = st.session_state["results"]["post"]

    elif st.session_state["results"]["post"]:
        result_type = "Post"
        doc_list = st.session_state["results"]["post"]
    else:
        result_type = "Comment"
        doc_list = st.session_state["results"]["comment"]

    with col:
        st.markdown(f"<h2 style='text-align: center;'>{result_type + 's'} on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        st.write('---')

    if not len(doc_list) > 0:
        if analysis_mode:
            _, message_col, _ = st.columns([1,5,1])
            with message_col:
                st.info("No results for current model and analysis setting.")

        else:
            display_no_result_message()
            return

    for doc in doc_list:

        if analysis_mode:
            
            if not doc[filter_category][0] == filter_value:
                continue

        # Display post
        with col.container(border=True):
            annotated_text(
                (f'Subreddit: {doc["subreddit_name"][0]}', "")
            )
            st.markdown(f"<p style='font-size:20px;'>User: {doc['author'][0]}</p>", unsafe_allow_html=True)
            if type == "Post":
                text = format_text(bold_matching_words(st.session_state["query"], doc['text'][0]))
                st.markdown(f"<p style='text-align: center;font-size:30px;'>{text}</p>", unsafe_allow_html=True)
            else:
                text = format_text(bold_matching_words(st.session_state["query"], doc['text'][0]))
                st.markdown(f"<p style='text-align: center;font-size:25px;'>{text}</p>", unsafe_allow_html=True)


            st.write(f'{doc["upvote"][0]} **Upvotes**  **·**  Posted on: {datetime.datetime.strptime(doc["created_utc"][0], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %B %Y, %I:%M%p")}')
            st.link_button(f"Link to {result_type}", "https://www.reddit.com"+doc['permalink'][0])

            st.write('---')

            display_mood_subjectivity(doc, 18, 15)

def display_wordcloud(word_freq_dict, label_category, model_selection):

    query_tokens = get_tokens_freq_dict(st.session_state["query"], "list")
    filtered_dict = {key: value for key, value in word_freq_dict.items() if key not in query_tokens}

    # Create and generate a word cloud image:
    wc = WordCloud(background_color="rgba(255, 255, 255, 0)", mode="RGBA", min_font_size = 10)
    wordcloud = wc.generate_from_frequencies(filtered_dict)

    fig, ax = plt.subplots()
    ax.set_title(f"WordCloud of {label_category} according to {model_selection}")
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

def display_no_result_message():
    _, message_col, _ = st.columns([1,5,1])
    with message_col:
        st.info("No results. Perhaps check your spelling or change the additional options?")

def display_post_and_comment():

    st.markdown(f"<h2 style='text-align: center;'>Posts and Comments on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
    st.write('---')

    if not len(st.session_state["results"]["post"]) > 0:
        display_no_result_message()
        return

    post_col, comment_col= st.columns([1,1])

    for i in range(len(st.session_state["results"]["post"])):
        tmp_post = st.session_state["results"]["post"][i]
        tmp_comment_list = st.session_state["results"]["comment"][i]

        # Display post
        with post_col.container(border=False, height=600):
            annotated_text(
                (f'Subreddit: {tmp_post["subreddit_name"][0]}', "")
            )
            st.markdown(f"<p style='font-size:20px;'>User: {tmp_post['author'][0]}</p>", unsafe_allow_html=True)

            text = format_text(bold_matching_words(st.session_state["query"], tmp_post['text'][0]))
            st.markdown(f"<p style='text-align: center;font-size:30px;'>{text}</p>", unsafe_allow_html=True)

            st.write(f'{tmp_post["upvote"][0]} **Upvotes**  **·**  Posted on: {datetime.datetime.strptime(tmp_post["created_utc"][0], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %B %Y, %I:%M%p")}')
            st.link_button("Link to Post", "https://www.reddit.com"+tmp_post['permalink'][0])

            st.write('---')

            display_mood_subjectivity(tmp_post, 18, 15)
            
        with post_col:
            st.write('---')

        with comment_col.container(border=True, height=600):
            st.markdown(f"<h3>Comments:</h3>", unsafe_allow_html=True)
            if len(tmp_comment_list) > 0:
                for comment in tmp_comment_list:
                    with st.container(border=True):
                        st.markdown(f"<p style='font-size:15px;'>User: {comment['author'][0]}</p>", unsafe_allow_html=True)
                        # st.markdown(f"<p style='text-align: center;font-size:20px;'>{comment['text'][0]}</p>", unsafe_allow_html=True)

                        text = format_text(bold_matching_words(st.session_state["query"], comment['text'][0]))
                        st.markdown(f"<p style='text-align: center;font-size:20px;'>{text}</p>", unsafe_allow_html=True)

                        st.write(f'{comment["upvote"][0]} **Upvotes**  **·**  Posted on: {datetime.datetime.strptime(comment["created_utc"][0], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %B %Y, %I:%M%p")}')
                        st.link_button("Link to Comment", "https://www.reddit.com"+comment['permalink'][0])

                        st.write('---')

                        display_mood_subjectivity(comment, 18, 15)
            else:
                st.write("No comments available.")

        with comment_col:
            st.write('---')
    