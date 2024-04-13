import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from collections import Counter
import time

from solr_utils.solr_manager import SolrManager
from streamlit_utils.st_utils import (display_post_and_comment, display_no_result_message,
                                      display_single_only, get_results, init_session_states,
                                      suggest_spell_correction, display_analysis)


# Set up Solr Core
solr_manager = SolrManager(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "solr-9.5.0-slim"),
                           os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data/merged_all_new.csv"))


tokens_init_format = {
            "vader_positive": Counter(),
            "vader_neutral": Counter(),
            "vader_negative": Counter(),
            "vader_subjective": Counter(),
            "vader_objective": Counter(),
            "textblob_positive": Counter(),
            "textblob_neutral": Counter(),
            "textblob_negative": Counter(),
            "textblob_subjective": Counter(),
            "textblob_objective": Counter(),
            "roberta_positive": Counter(),
            "roberta_neutral": Counter(),
            "roberta_negative": Counter()
        }

label_init_format = {
            "vader_positive": 0,
            "vader_neutral": 0,
            "vader_negative": 0,
            "vader_subjective": 0,
            "vader_objective": 0,
            "textblob_positive": 0,
            "textblob_neutral": 0,
            "textblob_negative": 0,
            "textblob_subjective": 0,
            "textblob_objective": 0,
            "roberta_positive": 0,
            "roberta_neutral": 0,
            "roberta_negative": 0
        }

# Page setup
st.set_page_config(page_title="Reddit EV Opinion Search", page_icon=":car:", layout="wide")

init_session_states()

st.markdown("<h1 style='text-align: center;'>&#128663 Reddit Electrical Vehicle Opinion Search</h1>", unsafe_allow_html=True)

_,search_col,_ = st.columns([1,2,1])
with search_col:
    query = st.text_input("Enter keywords:", value="")
    _, button_col = st.columns([6,1])
    with button_col:
        search_button = st.button("Search", type="primary")

with st.sidebar:
    st.subheader("Additional options:")
    st.write("\* *Please click 'Search' to search with the additional options.*")
    exact_matching = st.checkbox("Tick to search for the exact phrase")
    with st.expander("Date range"):
        date_left_col, date_right_col = st.columns([1,1])
        with date_left_col:
            date_start = st.date_input("Select date to retrieve opinions from:", value=None, format="MM/DD/YYYY")
        with date_right_col:
            date_end = st.date_input("Select date to retrieve opinions till:", value=None, format="MM/DD/YYYY")

    with st.expander("Retrieve types:"):
        retrieve_type = st.radio(
            "Retrieve:",
            ["Comments only", "Posts only", "Posts and Comments (Will take a longer time)"])

    with st.expander("Number of results to retrieve:"):
        retrieve_num = st.slider("Choose the number of post/comments to retrieve:", 5, 30, 10)
        st.write("Please take note that increasing the number of post/comments to retrieve will increase the loading time.")


if search_button or st.session_state["search_suggested"]:
    if not query and not st.session_state["search_suggested"]:
        st.info("Please enter keywords.")
    else:
        cur_options = {
                "exact_matching" : exact_matching,
                "date_start" : date_start,
                "date_end" : date_end,
                "retrieve_type" : retrieve_type,
                "retrieve_num" : retrieve_num
            }

        # If not the same query as previous, update query and additional options, and start searching
        if not st.session_state["additional_options"] == cur_options or not st.session_state["query"] == query:
            with st.spinner("Loading..."):
                st.session_state["additional_options"] = cur_options
                st.session_state["query"] = query

                start_time = time.time()
                # Get results for current query
                get_results(solr_manager, tokens_init_format, label_init_format)
                st.session_state["query_time"] = time.time() - start_time
        
        elif st.session_state["search_suggested"]:
            with st.spinner("Loading..."):
                st.session_state["additional_options"] = cur_options
                st.session_state["query"] = st.session_state["suggested_query"]
                st.session_state["suggested_query"] = None
                st.session_state["search_suggested"] = False

                start_time = time.time()
                # Get results for current query
                get_results(solr_manager, tokens_init_format, label_init_format)
                st.session_state["query_time"] = time.time() - start_time
        
        # Else, do nothing.

# if not query:
if not st.session_state["results"]:
    st.write('---')
    _,info_col,_ = st.columns([1,2,1])
    with info_col:
        st.info("Please type in keywords and click 'Search' to start.")
# If there is stored results, display it
else:
    tab1, tab2 = st.container().tabs(["Opinions on Reddit", "Text Analysis"])

    if len(st.session_state["results"]["post"]) > 0 and len(st.session_state["results"]["comment"]) > 0:
        tmp_display_state = "posts and comments"  
    elif len(st.session_state["results"]["post"]) > 0 or len(st.session_state["results"]["comment"]) > 0:
        tmp_display_state = "single only" 
    else:
        tmp_display_state = "no results"

    with tab1:
        # To display on top when there are results
        if st.session_state["suggested_query"] and not tmp_display_state == "no results":
            suggest_spell_correction(button_id="tab1")

        if tmp_display_state == "posts and comments":
            st.write(f"Retrieved results in: {st.session_state['query_time']:.2f} sec")
            display_post_and_comment()     
        elif tmp_display_state == "single only":
            st.write(f"Retrieved results in: {st.session_state['query_time']:.2f} sec")
            display_single_only()
        else:
            display_no_result_message()
            # To display below message if no results
            if st.session_state["suggested_query"]:
                suggest_spell_correction(button_id="tab1_no_result")

    with tab2:
        if st.session_state["suggested_query"] and not tmp_display_state == "no results":
            suggest_spell_correction(button_id="tab2")

        if tmp_display_state == "no results":
            display_no_result_message()
            # To display below message if no results
            if st.session_state["suggested_query"]:
                suggest_spell_correction(button_id="tab2_no_result")

        else:
            _,col1,col2,_ = st.columns([1,1,1,1])
            with col1:
                model_selection = st.radio(
                    "Use which model's results?",
                    ["VADER", "TextBlob", "roBERTa-based"]
                )
            with col2:
                label_category = st.radio(
                    "Analyse on which category?",
                    ["Positive Mood", "Neutral Mood", "Negative Mood", "Subjective", "Objective"]
                )
            st.write('---')

            display_analysis(model_selection, label_category)

css = '''
    <style>
button[data-baseweb="tab"] {
font-size: 24px;
margin: 0;
width: 100%;
}
</style>
    '''

st.markdown(css, unsafe_allow_html=True)