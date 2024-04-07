import streamlit as st
import datetime
import matplotlib.pyplot as plt

from annotated_text import annotated_text
from wordcloud import WordCloud

from utils.utils import get_tokens, bold_matching_words, format_text

def display_post_and_comment(solr_manager, query, doc, post_col, comment_col):

    tokens = []

    # print(doc)

    # Display post
    with post_col.container(border=False, height=500):
        annotated_text(
            (f'Subreddit: {doc["subreddit_name"][0]}', "")
        )
        st.markdown(f"<p style='font-size:20px;'>User: {doc['author'][0]}</p>", unsafe_allow_html=True)

        # st.markdown(f"<p style='text-align: center;font-size:30px;'>{doc['text'][0]}</p>", unsafe_allow_html=True)
        text = format_text(bold_matching_words(query, doc['text'][0]))
        st.markdown(f"<p style='text-align: center;font-size:30px;'>{text}</p>", unsafe_allow_html=True)

        st.write(f'{doc["upvote"][0]} **Upvotes**  **·**  Posted on: {datetime.datetime.strptime(doc["created_utc"][0], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %B %Y, %I:%M%p")}')
        st.link_button("Link to Post", "https://www.reddit.com"+doc['permalink'][0])
    with post_col:
        st.write('---')

    # Get tokens from post
    tokens = tokens + get_tokens(doc['text'][0])

    # Display comments
    with comment_col.container(border=True, height=500):
        st.markdown(f"<h3>Comments:</h3>", unsafe_allow_html=True)
        comment_list = solr_manager.get_comment_from_post_id_and_text(doc["id"], query)
        # print("comment_list:")
        # print(comment_list)
        if len(comment_list) > 0:
            for comment in comment_list:
                # print(comment)
                with st.container(border=True):
                    st.markdown(f"<p style='font-size:15px;'>User: {comment['author'][0]}</p>", unsafe_allow_html=True)
                    # st.markdown(f"<p style='text-align: center;font-size:20px;'>{comment['text'][0]}</p>", unsafe_allow_html=True)

                    text = format_text(bold_matching_words(query, comment['text'][0]))
                    st.markdown(f"<p style='text-align: center;font-size:20px;'>{text}</p>", unsafe_allow_html=True)

                    st.write(f'{comment["upvote"][0]} **Upvotes**  **·**  Posted on: {datetime.datetime.strptime(comment["created_utc"][0], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %B %Y, %I:%M%p")}')
                    st.link_button("Link to Comment", "https://www.reddit.com"+comment['permalink'][0])

                    # Get tokens from comments
                    tokens = tokens + get_tokens(comment['text'][0])
        else:
            st.write("No comments available.")

    with comment_col:
        st.write('---')

    return tokens

def display_single_only(query, doc, col, type):

    tokens = []

    # Display post
    with col.container(border=True):
        annotated_text(
            (f'Subreddit: {doc["subreddit_name"][0]}', "")
        )
        st.markdown(f"<p style='font-size:20px;'>User: {doc['author'][0]}</p>", unsafe_allow_html=True)
        if type == "Post":
            # st.markdown(f"<p style='text-align: center;font-size:30px;'>{doc['text'][0]}</p>", unsafe_allow_html=True)

            text = format_text(bold_matching_words(query, doc['text'][0]))
            st.markdown(f"<p style='text-align: center;font-size:30px;'>{text}</p>", unsafe_allow_html=True)
        else:
            # st.markdown(f"<p style='text-align: center;font-size:25px;'>{doc['text'][0]}</p>", unsafe_allow_html=True)

            text = format_text(bold_matching_words(query, doc['text'][0]))
            st.markdown(f"<p style='text-align: center;font-size:25px;'>{text}</p>", unsafe_allow_html=True)


        st.write(f'{doc["upvote"][0]} **Upvotes**  **·**  Posted on: {datetime.datetime.strptime(doc["created_utc"][0], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %B %Y, %I:%M%p")}')
        st.link_button(f"Link to {type.capitalize()}", "https://www.reddit.com"+doc['permalink'][0])

    # Get tokens from post
    tokens = tokens + get_tokens(doc['text'][0])

    return tokens


def display_wordcloud(tokens, query):

    query_tokens = get_tokens(query)
    tokens = [word for word in tokens if word not in query_tokens]

    word_string = ' '.join(tokens)

    # Create and generate a word cloud image:
    wc = WordCloud(background_color="rgba(255, 255, 255, 0)", mode="RGBA", min_font_size = 10)
    wordcloud = wc.generate(word_string)

    # Display the generated image:
    _, col1, _ = st.columns([1,3,1])
    with col1:
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

def display_no_result_message():
    _, message_col, _ = st.columns([1,1.1,1])
    with message_col:
        st.info("No results. Perhaps check your spelling or change the additional options?")