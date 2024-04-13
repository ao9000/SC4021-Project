# SC4021 Information Retrieval-Group 24

## Group Members
| Name | Matriculation Number |
| --- | -- |
| Ong Zhi Ying, Adrian | U2121883A |
| Takesawa Saori | U2023120E |
| Cheong Yong Wen | U2021159L |
| Kwok Zong Heng | U2021027E |
| Mandfred Leow Hong Jie | U2122023G |


## Project Overview
By 2030, Singapore aims to have a significant portion of its vehicle population comprised of electric vehicles (EVs) as part of its commitment to combat climate change. Given the incentives to switch to EVs, members of the public will soon need to decide on the brand and model of EV to purchase. To assist with this decision-making process, this project aims to design and develop an information retrieval system that can search and display public user comments related to EV brands and models from various social platforms. Additionally, the system will derive deeper insights using Natural Language Processing techniques such as sentiment analysis, subjectivity, and sarcasm classification.

## Technical Overview
The project is divided into 4 main components:
1. Web crawling
1. Data Indexing (Backend)
1. Frontend UI
1. Classification

## Pre-requisites to run the code (Exact )
1. Python 3.8.5
1. Curl 8.4.0
1. Apache Solr 9.5.0
1. Java 1.8.0_401

## Instructions to run the code
- Firstly, change directory into the base directory using ```cd SC4021-Project``` and install all required libraries using ```pip install -r requirements.txt```
- Make sure you have the correct venu or conda environment activated

### Web crawling
1. Run ```reddit-data-extraction.ipynb``` -> This notebook contains step by step codes for extracting/crawling data from Reddit using predefined subreddits
1. After crawling the data, run ```data-processing-for-solr.ipynb``` -> Executes basic data pre-processing

#### Structure of crawled data
- {subreddit_name}-posts.csv -> Contains the top 100 posts from the subreddit
- {subreddit_name}-comments.csv -> Contains all the comments associated with the top 100 posts of the subreddit
- all-post.csv -> Contains the combined posts from all subreddits
- all-comments.csv -> Contains the combined comments from all subreddits
- cleaned_combined_data.csv -> Contains both the posts and comments (Normalized) from all subreddits after cleaning

### Data Indexing (Backend)
1. Make sure environment variable ```$JAVA_HOME``` is set to the correct Java JDK
1. Make sure environment variable ```$PATH``` is set to the correct Apache Solr directory
1. Open up CMD and run ```solr start```
1. You can navigate to ```localhost:8983/solr``` to access GUI for Apache Solr, however we will be using Curl to communicate with Solr
1. Navigate to the jupyter notebook ```add_solr_schema.ipynb``` and run the cells to index the data into Apache Solr

### Frontend UI
1. Start solr server by running ```solr start``` in the terminal
1. Navigate to the frontend directory by running ```cd search_engine```
1. Run ```python app.py``` to start the streamlit app

### Classification
Different classification innovations are implemented in various notebooks. The notebooks are as follows:
1. ```Polarity_and_subjectivity_Detection.ipynb``` -> This notebook contains the code for detecting the polarity and subjectivity of the comments
1. ```inter_annotation_agreement.ipynb``` -> This notebook contains the code for calculating the inter-annotator agreement
1. ```classification.ipynb``` -> This notebook contains the code for ensembling techniques and testing of different sentiment classification models

#### Labelled data
- ```popular_comment_Bolt_YWAnnotate.csv``` -> Contains the labelled data for the Bolt EV labelled by 1 annotator
- ```popular_comment_Bolt_zh_annotate.csv``` -> Contains the labelled data for the Bolt EV labelled by 1 annotator
- ```popular_comment_Bolt_annotate_Merged.csv``` -> Contains the labelled data for the Bolt EV labelled by 2 annotators
