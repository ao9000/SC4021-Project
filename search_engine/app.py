import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from ast import literal_eval
from wordcloud import WordCloud
from annotated_text import annotated_text
from collections import Counter

from solr_utils.solr_manager import SolrManager
from streamlit_utils.st_utils import display_post_and_comment, display_wordcloud, display_no_result_message, display_single_only
from utils.utils import update_tokens_and_labels


# Set up Solr Core
solr_manager = SolrManager(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "solr-9.5.0-slim"),
                           os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data/(copy)VadersTextBlobCombinedData.csv"))

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

def suggest_diff_query(solr_manager):
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

def display_results(retrieve_type, exact_matching):

    # tokens = []

    if retrieve_type == "Posts and Comments (Will take a longer time)":
        st.markdown(f"<h2 style='text-align: center;'>Posts and Comments on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        result_type = 'post'
    elif retrieve_type == "Posts only":
        st.markdown(f"<h2 style='text-align: center;'>Posts on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        result_type = 'post'
    else:
        st.markdown(f"<h2 style='text-align: center;'>Comments on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        result_type = 'comment'

    st.write('---')

    if exact_matching:
        results = solr_manager.get_text_query_result(st.session_state["query"], result_type, tmp_date_range, phrase_search=True, num_rows=retrieve_num)
    else:
        results = solr_manager.get_text_query_result(st.session_state["query"], result_type, tmp_date_range, num_rows=retrieve_num)

    if results["response"]["numFound"] < retrieve_num:
        suggested_query = suggest_diff_query(solr_manager, st.session_state["query"], result_type, tmp_date_range, retrieve_num)
    else:
        suggested_query = None

    if results["response"]["numFound"] == 0 and not suggested_query:
        display_no_result_message()
        st.session_state["results"] = None

    elif results["response"]["numFound"] == 0 and suggested_query:
        suggest_spell_correction(suggested_query, True)
        st.session_state["results"] = None

    else:
        if suggested_query:
            suggest_spell_correction(suggested_query, False)

        if retrieve_type == "Posts and Comments (Will take a longer time)":
            comment_list = []
            st.write("")
            st.write("")
            post_col, comment_col= st.columns([1,1])
            for doc in results["response"]["docs"]:
                # tokens = tokens + display_post_and_comment(solr_manager, st.session_state["query"], doc, post_col, comment_col)
                comment_list = comment_list + display_post_and_comment(solr_manager, st.session_state["query"], doc, post_col, comment_col)

            st.session_state["results"] = {"post": results["response"]["docs"], "comment": comment_list}


        else:
            st.write("")
            st.write("")
            _, post_col, _= st.columns([1,5,1])
            for doc in results["response"]["docs"]:
                # tokens = tokens + display_single_only(st.session_state['query'], doc, post_col, result_type)
                display_single_only(st.session_state['query'], doc, post_col, result_type)

            if result_type == 'post':
                st.session_state["results"] = {"post": results["response"]["docs"], "comment": None}
            else:
                st.session_state["results"] = {"post": None, "comment": results["response"]["docs"]}

def get_results():

    # tokens = []
    st.session_state["tokens"] = tokens_init_format
    st.session_state["label_count"] = label_init_format

    if st.session_state["additional_options"]["retrieve_type"] == "Posts and Comments (Will take a longer time)":
        # st.markdown(f"<h2 style='text-align: center;'>Posts and Comments on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        result_type = 'post'
    elif st.session_state["additional_options"]["retrieve_type"] == "Posts only":
        # st.markdown(f"<h2 style='text-align: center;'>Posts on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        result_type = 'post'
    else:
        # st.markdown(f"<h2 style='text-align: center;'>Comments on Reddit about \"{st.session_state['query']}\":</h2>", unsafe_allow_html=True)
        result_type = 'comment'

    st.write('---')

    tmp_date_start = st.session_state["additional_options"]["date_start"]
    tmp_date_end = st.session_state["additional_options"]["date_end"]

    # Date range for querying
    min_date = datetime.date(2016, 12, 19) # min date in csv
    max_date = datetime.date(2024, 3, 22) # max date in csv

    if tmp_date_start and tmp_date_end:
        tmp_date_range = [str(tmp_date_start.strftime('%Y-%m-%d')), str(tmp_date_end.strftime('%Y-%m-%d'))]
    elif date_start and not date_end:
        tmp_date_range = [str(tmp_date_start.strftime('%Y-%m-%d')), str(max_date.strftime('%Y-%m-%d'))]
    elif not date_start and date_end:
        tmp_date_range = [str(min_date.strftime('%Y-%m-%d')), str(tmp_date_end.strftime('%Y-%m-%d'))]
    else:
        tmp_date_range = None

    if st.session_state["additional_options"]["exact_matching"]:
        results = solr_manager.get_text_query_result(st.session_state["query"], result_type, tmp_date_range, phrase_search=True, num_rows=retrieve_num)
    else:
        results = solr_manager.get_text_query_result(st.session_state["query"], result_type, tmp_date_range, num_rows=retrieve_num)

    if results["response"]["numFound"] < retrieve_num:
        st.session_state["suggested_query"] = suggest_diff_query(solr_manager)
    else:
        st.session_state["suggested_query"] = None

    if results["response"]["numFound"] == 0 and not st.session_state["suggested_query"]:
        # display_no_result_message()
        st.session_state["results"] = {"post": [], "comment": []}

    elif results["response"]["numFound"] == 0 and st.session_state["suggested_query"]:
        # suggest_spell_correction(suggested_query, True)
        st.session_state["results"] = {"post": [], "comment": []}

    else:
        # if suggested_query:
        #     suggest_spell_correction(suggested_query, False)

        if st.session_state["additional_options"]["retrieve_type"] == "Posts and Comments (Will take a longer time)":
            comment_list = []
            # st.write("")
            # st.write("")
            # post_col, comment_col= st.columns([1,1])
            for doc in results["response"]["docs"]:
                # tokens = tokens + display_post_and_comment(solr_manager, st.session_state["query"], doc, post_col, comment_col)
                # comment_list = comment_list + display_post_and_comment(solr_manager, st.session_state["query"], doc, post_col, comment_col)
                update_tokens_and_labels(doc)

                comment_list = comment_list.append(solr_manager.get_comment_from_post_id_and_text(doc["id"], query))
                for comment in comment_list:
                    update_tokens_and_labels(comment)


            st.session_state["results"] = {"post": results["response"]["docs"], "comment": comment_list}

        else:
            # st.write("")
            # st.write("")
            # _, post_col, _= st.columns([1,5,1])
            # for doc in results["response"]["docs"]:
            #     tokens = tokens + display_single_only(st.session_state['query'], doc, post_col, result_type)
            #     display_single_only(st.session_state['query'], doc, post_col, result_type)

            if result_type == 'post':
                st.session_state["results"] = {"post": results["response"]["docs"], "comment": []}
            else:
                st.session_state["results"] = {"post": [], "comment": results["response"]["docs"]}
                print("inside get_results():")
                print(st.session_state)

            for doc in results["response"]["docs"]:
                update_tokens_and_labels(doc)

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
            "textblob_objective": Counter()
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
            "textblob_objective": 0
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
    exact_matching = st.checkbox("Tick to search for the exact phrase")
    with st.expander("Date range"):
        date_left_col, date_right_col = st.columns([1,1])
        with date_left_col:
            date_start = st.date_input("Select date to retrieve opinions from:", value=None, format="MM/DD/YYYY")
        with date_right_col:
            date_end = st.date_input("Select date to retrieve opinions till:", value=None, format="MM/DD/YYYY")
    # st.write('---')

    with st.expander("Retrieve types:"):
        retrieve_type = st.radio(
            "Retrieve:",
            ["Comments only", "Posts only", "Posts and Comments (Will take a longer time)"])
    # st.write('---')

    with st.expander("Number of results to retrieve:"):
        retrieve_num = st.slider("Choose the number of post/comments to retrieve:", 5, 30, 10)
        st.write("Please take note that increasing the number of post/comments to retrieve will increase the loading time.")


if search_button or st.session_state["search_suggested"]:
    print("pressed search button")
    if not query and not st.session_state["search_suggested"]:
        st.info("Please enter keywords.")
    else:
        print("inside search button pressed else side")
        cur_options = {
                "exact_matching" : exact_matching,
                "date_start" : date_start,
                "date_end" : date_end,
                "retrieve_type" : retrieve_type
            }

        # If not the same query as previous, update query and additional options, and start searching
        if not st.session_state["additional_options"] == cur_options or not st.session_state["query"] == query:
            print("inside updating query")
            with st.spinner("Loading..."):
                st.session_state["additional_options"] = cur_options
                st.session_state["query"] = query

                # Get results for current query
                get_results()
        
        elif st.session_state["search_suggested"]:
            with st.spinner("Loading..."):
                st.session_state["additional_options"] = cur_options
                st.session_state["query"] = st.session_state["suggested_query"]
                st.session_state["suggested_query"] = None
                st.session_state["search_suggested"] = False

                # Get results for current query
                get_results()
        
        # Else, do nothing.

# if not query:
if not st.session_state["results"]:
    st.write('---')
    _,info_col,_ = st.columns([1,2,1])
    with info_col:
        st.info("Please type in keywords and click 'Search' to start.")
# If there is stored results, display it
else:
    tab1, tab2, tab3 = st.container().tabs(["Opinions on Reddit", "[Not decided yet]", "Word Cloud"])

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
            display_post_and_comment()     
        elif tmp_display_state == "single only":
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
                    ["VADER", "TextBlob"]
                )
            with col2:
                label_category = st.radio(
                    "Analyse on which category?",
                    ["Positive Mood", "Neutral Mood", "Negative Mood", "Subjective", "Objective"]
                )
            st.write('---')

            

    with tab3:
        if st.session_state["suggested_query"] and not tmp_display_state == "no results":
            suggest_spell_correction(button_id="tab3")

        if tmp_display_state == "no results":
            display_no_result_message()
            # To display below message if no results
            if st.session_state["suggested_query"]:
                suggest_spell_correction(button_id="tab3_no_result")

    
    

print("st.session_state outside 1:")
print(st.session_state)

# if (query and search_button):
#     print("st.session_state in changing part:")
#     st.session_state["query"] = query
#     st.session_state["search_pressed"] = True
#     print(st.session_state)


# if (st.session_state["query"] and st.session_state["search_pressed"]):

#     with st.spinner("Loading..."):

#         tab1, tab2, tab3 = st.container().tabs(["Opinions on Reddit", "[Not decided yet]", "Word Cloud"])

#         with tab1:

#             if date_start and date_end:
#                 tmp_date_range = [str(date_start.strftime('%Y-%m-%d')), str(date_end.strftime('%Y-%m-%d'))]
#             elif date_start and not date_end:
#                 tmp_date_range = [str(date_start.strftime('%Y-%m-%d')), str(max_date.strftime('%Y-%m-%d'))]
#             elif not date_start and date_end:
#                 tmp_date_range = [str(min_date.strftime('%Y-%m-%d')), str(date_end.strftime('%Y-%m-%d'))]
#             else:
#                 tmp_date_range = None

#             tokens = display_results(retrieve_type, exact_matching)

#         with tab2:
#             st.markdown(f"<h2 style='text-align: center;'>Reddit Comments about \"{query}\":</h2>", unsafe_allow_html=True)

#             negative_tab, neutral_tab, positive_tab = st.tabs(["Negative Opinions", "Neutral Opinions", "Positive Opinions"])
#             with negative_tab:
                

#             # with tab1:
#                 # st.markdown(f"<h2 style='text-align: center;'>Impressions about \"{query}\" on the net:</h2>", unsafe_allow_html=True)
#                 # # Calculate percentage of good and bad
#                 # fig, ax = plt.subplots()
#                 # gd_percent = df_search['test_senti'].value_counts()['Good'] / len(df_search) * 100
#                 # bad_percent = 100-gd_percent
#                 # patches, _, _ = ax.pie([bad_percent, gd_percent], labels=['Bad', 'Good'], colors=['darksalmon', 'palegreen'] ,autopct='%1.1f%%', startangle=90, explode=[0.05, 0.05])
#                 # patches[0].set_edgecolor('navy')
#                 # patches[1].set_edgecolor('navy')

#                 # if st.session_state["sort_by"] == 'upvotes':
#                 #     df_search.sort_values(by='score', ascending=False)
#                 # else:
#                 #     df_search.sort_values(by='score', ascending=True)

#                 # col1,col2,col3 = st.columns([1,1,1])
#                 # with col1:
#                 #     st.subheader("Negative Opinions:")
#                 #     tag_col1, tag_col2, tag_col3 =st.columns([1,2,2])
#                 #     with tag_col1:
#                 #         st.text("Tags:")
#                 #     with tag_col2:
#                 #         st.button("bad")
#                 #     with tag_col3:
#                 #         st.button("inefficient")

#                 #     bad_side_container = st.container(border=True, height=500)
#                 #     bad_df = df_search.loc[df_search['test_senti']=='Bad']

#                 #     for i in range(len(bad_df)):
#                 #         comment_box = bad_side_container.container(border=True)
#                 #         comment_box.write(bad_df.iloc[i]['body'])
#                 #         comment_box.link_button("Link to comment", "https://www.reddit.com"+bad_df.iloc[i]['permalink'])
#                 # with col2:
#                 #     st.pyplot(fig)
#                 #     st.markdown(f"<h4 style='text-align: center;'>Sort by:</h4>", unsafe_allow_html=True)
#                 #     _, subcol1, subcol2, subcol3, _ = st.columns([1,2,2,2,1])
#                 #     with subcol1:
#                 #         if st.session_state['sort_by'] == 'upvotes':
#                 #             sort_by_upvote = st.button("Upvotes", type='primary')
#                 #         else:
#                 #             sort_by_upvote = st.button("Upvotes")
#                 #     with subcol2:
#                 #         if st.session_state['sort_by'] == 'senti_score':
#                 #             sort_by_senti_score = st.button("Sentiment score", type='primary')
#                 #         else:
#                 #             sort_by_senti_score = st.button("Sentiment score")
#                 #     with subcol3:
#                 #         if st.session_state['sort_by'] == 'word_length':
#                 #             sort_by_length = st.button("Word length", type='primary')
#                 #         else:
#                 #             sort_by_length = st.button("Word length")

#                 # if sort_by_upvote:
#                 #     st.session_state['sort_by'] = 'upvotes'
#                 # elif sort_by_senti_score:
#                 #     st.session_state['sort_by'] = 'senti_score'
#                 # elif sort_by_length:
#                 #     st.session_state['sort_by'] = 'word_length'

#                 # with col3:
#                 #     st.subheader("Positive Opinions:")
#                 #     tag_col1, tag_col2, tag_col3 =st.columns([1,2,2])
#                 #     with tag_col1:
#                 #         st.text("Tags:")
#                 #     with tag_col2:
#                 #         st.button("awesome")
#                 #     with tag_col3:
#                 #         st.button("nice")
#                 #     gd_side_container = st.container(border=True, height=500)
#                 #     gd_df = df_search.loc[df_search['test_senti']=='Good']

#                 #     for i in range(len(gd_df)):
#                 #         comment_box = gd_side_container.container(border=True)
#                 #         comment_box.write(gd_df.iloc[i]['body'])
#                 #         comment_box.link_button("Link to comment", "https://www.reddit.com"+gd_df.iloc[i]['permalink'])
        
#         with tab3:
#             if len(tokens) == 0:
#                 display_no_result_message()
#             else:
#                 display_wordcloud(tokens, st.session_state["query"])

#         # If current search was after spellcheck search
#         if st.session_state["suggested_query"]:
#             st.session_state["search_pressed"] = False

        

css = '''
    <style>
button[data-baseweb="tab"] {
font-size: 24px;
margin: 0;
width: 100%;
}
</style>
    '''

print(" at the bottom:")
print(st.session_state)
print()
print()
st.markdown(css, unsafe_allow_html=True)


