import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from ast import literal_eval
from wordcloud import WordCloud
from annotated_text import annotated_text

from solr_utils.solr_manager import SolrManager
from streamlit_utils.st_utils import display_post_and_comment, display_wordcloud


# Set up Solr Core
solr_manager = SolrManager(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "solr-9.5.0-slim"),
                           os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data/cleaned_combined_data.csv"))

# Date range for querying
min_date = datetime.date(2016, 12, 19) # min date in csv
max_date = datetime.date(2024, 3, 22) # max date in csv


# Page setup
st.set_page_config(page_title="Reddit EV Opinion Search", page_icon=":car:", layout="wide")

if 'sort_by' not in st.session_state:
    st.session_state['sort_by'] = 'upvotes'

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
    search_button = st.button("Search")

if not query:
    _,info_col,_ = st.columns([1,2,1])
    with info_col:
        st.info("Please type in keywords and click 'Search' to start.")


if query and search_button:
    with st.spinner("Loading..."):

        tab1, tab2, tab3 = st.container().tabs(["Reddit Posts", "[Not decided yet]", "Word Cloud"])

        with tab1:
            st.markdown(f"<h2 style='text-align: center;'>Opinions on Reddit about \"{query}\":</h2>", unsafe_allow_html=True)
            st.write('---')

            if date_start and date_end:
                tmp_date_range = [str(date_start.strftime('%Y-%m-%d')), str(date_end.strftime('%Y-%m-%d'))]
            elif date_start and not date_end:
                tmp_date_range = [str(date_start.strftime('%Y-%m-%d')), str(max_date.strftime('%Y-%m-%d'))]
            elif not date_start and date_end:
                tmp_date_range = [str(min_date.strftime('%Y-%m-%d')), str(date_end.strftime('%Y-%m-%d'))]
            else:
                tmp_date_range = None

            post_results = solr_manager.get_text_query_result(query, 'post', tmp_date_range)

            post_col, comment_col= st.columns([1,1])

            if post_results["response"]["numFound"] == 0:
                _, message_col, _ = st.columns([1,1,1])
                with message_col:
                    st.info("No results. Perhaps change the date range or check your spelling?")

            # Get more results with more lenient search if querying with phrase and results are less than 50
            elif len(query.split(" ")) and post_results["response"]["numFound"] < 50:
                post_results = solr_manager.get_text_query_result(query, 'post', tmp_date_range, phrase_search=False)

                for doc in post_results["response"]["docs"]:
                    tokens = display_post_and_comment(solr_manager, query, doc, post_col, comment_col)
            else:
                for doc in post_results["response"]["docs"]:
                    tokens = display_post_and_comment(solr_manager, query, doc, post_col, comment_col)

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
            display_wordcloud(tokens, query)

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


