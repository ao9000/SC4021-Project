import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from ast import literal_eval
from wordcloud import WordCloud
from annotated_text import annotated_text

from solr_utils.solr_manager import SolrManager
from streamlit_utils.st_utils import display_post_and_comment, display_wordcloud, display_no_result_message, display_single_only


if "query" not in st.session_state:
    st.session_state["query"] = None

if "search_pressed" not in st.session_state:
    st.session_state["search_pressed"] = False

if "suggested_query" not in st.session_state:
    st.session_state["suggested_query"] = None

if "date_start" not in st.session_state:
    st.session_state["date_start"] = None

if "date_end" not in st.session_state:
    st.session_state["date_end"] = None

if "exact_matching" not in st.session_state:
    st.session_state["exact_matching"] = False

if "retrieve_type" not in st.session_state:
    st.session_state["retrieve_type"] = None

if "retrieve_num" not in st.session_state:
    st.session_state["retrieve_num"] = None

# Set up Solr Core
solr_manager = SolrManager(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "solr-9.5.0-slim"),
                           os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data/(copy)cleaned_combined_data.csv"))

# Date range for querying
min_date = datetime.date(2016, 12, 19) # min date in csv
max_date = datetime.date(2024, 3, 22) # max date in csv

def suggest_diff_query(solr_manager, query, type, date_range, num_rows):
    if not len(query.split(' ')) > 1:
        suggested_query = solr_manager.spellcheck(query)["spellcheck"]["suggestions"]
        # No spell suggestions
        if len(suggested_query) == 0:
            return None
        else:
            suggested_query = suggested_query[1]["suggestion"][0]["word"]
            return suggested_query
        
    else:
        return None

def suggest_spell_correction(suggested_query, no_result):
    _, message_col, _= st.columns([1,5,1])
    with message_col:
        if no_result:
            st.write(f"No results found for: {st.session_state['query']}. Did you mean: **{suggested_query}**?")
        else:
            st.write(f"Did you mean: **{suggested_query}**?")

        if st.button(f"Search with **{suggested_query}** instead"):
            st.session_state["suggested_query"] = suggested_query
            st.rerun()

def display_results(retrieve_type, exact_matching):

    tokens = []

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

    elif results["response"]["numFound"] == 0 and suggested_query:
        suggest_spell_correction(suggested_query, True)

    else:
        if suggested_query:
            suggest_spell_correction(suggested_query, False)

        if retrieve_type == "Posts and Comments (Will take a longer time)":
            st.write("")
            st.write("")
            post_col, comment_col= st.columns([1,1])
            for doc in results["response"]["docs"]:
                tokens = tokens + display_post_and_comment(solr_manager, st.session_state["query"], doc, post_col, comment_col)

        else:
            st.write("")
            st.write("")
            _, post_col, _= st.columns([1,5,1])
            for doc in results["response"]["docs"]:
                tokens = tokens + display_single_only(st.session_state['query'], doc, post_col, result_type)

    return tokens


# Page setup
st.set_page_config(page_title="Reddit EV Opinion Search", page_icon=":car:", layout="wide")


st.markdown("<h1 style='text-align: center;'>&#128663 Reddit Electrical Vehicle Opinion Search</h1>", unsafe_allow_html=True)

_,search_col,_ = st.columns([1,2,1])
with search_col:
    query = st.text_input("Enter keywords:", value="")
    with st.expander("Additional Options:"):
        date_left_col, date_right_col = st.columns([1,1])
        with date_left_col:
            date_start = st.date_input("Select date to retrieve opinions from:", value=None, format="MM/DD/YYYY")
        with date_right_col:
            date_end = st.date_input("Select date to retrieve opinions till:", value=None, format="MM/DD/YYYY")
        st.write('---')
        exact_matching = st.checkbox("Tick to search for the exact phrase")
        retrieve_type = st.radio(
            "Retrieve:",
            ["Comments only", "Posts only", "Posts and Comments (Will take a longer time)"])
        st.write('---')
        retrieve_num = st.slider("Choose the number of post/comments to retrieve:", 5, 30, 10)
        st.write("Please take note that increasing the number of post/comments to retrieve will increase the loading time.")
    _, button_col = st.columns([8,1])
    with button_col:
        search_button = st.button("Search", type="primary")

if not query:
    st.write('---')
    _,info_col,_ = st.columns([1,2,1])
    with info_col:
        st.info("Please type in keywords and click 'Search' to start.")

print("st.session_state outside 1:")
print(st.session_state)

if (query and search_button):
    print("st.session_state in changing part:")
    st.session_state["query"] = query
    st.session_state["search_pressed"] = True
    print(st.session_state)

if st.session_state["suggested_query"]:
    print("st.session_state in suggested query if:")
    st.session_state["query"] = st.session_state["suggested_query"]
    st.session_state["search_pressed"] = True
    print(st.session_state)


print("st.session_state outside 2:")
print(st.session_state)

if (st.session_state["query"] and st.session_state["search_pressed"]):

    with st.spinner("Loading..."):

        tab1, tab2, tab3 = st.container().tabs(["Opinions on Reddit", "[Not decided yet]", "Word Cloud"])

        with tab1:

            if date_start and date_end:
                tmp_date_range = [str(date_start.strftime('%Y-%m-%d')), str(date_end.strftime('%Y-%m-%d'))]
            elif date_start and not date_end:
                tmp_date_range = [str(date_start.strftime('%Y-%m-%d')), str(max_date.strftime('%Y-%m-%d'))]
            elif not date_start and date_end:
                tmp_date_range = [str(min_date.strftime('%Y-%m-%d')), str(date_end.strftime('%Y-%m-%d'))]
            else:
                tmp_date_range = None

            tokens = display_results(retrieve_type, exact_matching)

        with tab2:
            st.markdown(f"<h2 style='text-align: center;'>Reddit Comments about \"{query}\":</h2>", unsafe_allow_html=True)

            # with tab1:
                # st.markdown(f"<h2 style='text-align: center;'>Impressions about \"{query}\" on the net:</h2>", unsafe_allow_html=True)
                # # Calculate percentage of good and bad
                # fig, ax = plt.subplots()
                # gd_percent = df_search['test_senti'].value_counts()['Good'] / len(df_search) * 100
                # bad_percent = 100-gd_percent
                # patches, _, _ = ax.pie([bad_percent, gd_percent], labels=['Bad', 'Good'], colors=['darksalmon', 'palegreen'] ,autopct='%1.1f%%', startangle=90, explode=[0.05, 0.05])
                # patches[0].set_edgecolor('navy')
                # patches[1].set_edgecolor('navy')

                # if st.session_state["sort_by"] == 'upvotes':
                #     df_search.sort_values(by='score', ascending=False)
                # else:
                #     df_search.sort_values(by='score', ascending=True)

                # col1,col2,col3 = st.columns([1,1,1])
                # with col1:
                #     st.subheader("Negative Opinions:")
                #     tag_col1, tag_col2, tag_col3 =st.columns([1,2,2])
                #     with tag_col1:
                #         st.text("Tags:")
                #     with tag_col2:
                #         st.button("bad")
                #     with tag_col3:
                #         st.button("inefficient")

                #     bad_side_container = st.container(border=True, height=500)
                #     bad_df = df_search.loc[df_search['test_senti']=='Bad']

                #     for i in range(len(bad_df)):
                #         comment_box = bad_side_container.container(border=True)
                #         comment_box.write(bad_df.iloc[i]['body'])
                #         comment_box.link_button("Link to comment", "https://www.reddit.com"+bad_df.iloc[i]['permalink'])
                # with col2:
                #     st.pyplot(fig)
                #     st.markdown(f"<h4 style='text-align: center;'>Sort by:</h4>", unsafe_allow_html=True)
                #     _, subcol1, subcol2, subcol3, _ = st.columns([1,2,2,2,1])
                #     with subcol1:
                #         if st.session_state['sort_by'] == 'upvotes':
                #             sort_by_upvote = st.button("Upvotes", type='primary')
                #         else:
                #             sort_by_upvote = st.button("Upvotes")
                #     with subcol2:
                #         if st.session_state['sort_by'] == 'senti_score':
                #             sort_by_senti_score = st.button("Sentiment score", type='primary')
                #         else:
                #             sort_by_senti_score = st.button("Sentiment score")
                #     with subcol3:
                #         if st.session_state['sort_by'] == 'word_length':
                #             sort_by_length = st.button("Word length", type='primary')
                #         else:
                #             sort_by_length = st.button("Word length")

                # if sort_by_upvote:
                #     st.session_state['sort_by'] = 'upvotes'
                # elif sort_by_senti_score:
                #     st.session_state['sort_by'] = 'senti_score'
                # elif sort_by_length:
                #     st.session_state['sort_by'] = 'word_length'

                # with col3:
                #     st.subheader("Positive Opinions:")
                #     tag_col1, tag_col2, tag_col3 =st.columns([1,2,2])
                #     with tag_col1:
                #         st.text("Tags:")
                #     with tag_col2:
                #         st.button("awesome")
                #     with tag_col3:
                #         st.button("nice")
                #     gd_side_container = st.container(border=True, height=500)
                #     gd_df = df_search.loc[df_search['test_senti']=='Good']

                #     for i in range(len(gd_df)):
                #         comment_box = gd_side_container.container(border=True)
                #         comment_box.write(gd_df.iloc[i]['body'])
                #         comment_box.link_button("Link to comment", "https://www.reddit.com"+gd_df.iloc[i]['permalink'])
        
        with tab3:
            if len(tokens) == 0:
                display_no_result_message()
            else:
                display_wordcloud(tokens, st.session_state["query"])

        # If current search was after spellcheck search
        if st.session_state["suggested_query"]:
            st.session_state["search_pressed"] = False

        

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


