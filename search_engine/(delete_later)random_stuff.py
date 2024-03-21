import os
import pandas as pd
import random

import nltk
from nltk.stem import WordNetLemmatizer
nltk.download("wordnet")
nltk.download("omw-1.4")

# Initialize wordnet lemmatizer
wnl = WordNetLemmatizer()

df = pd.read_csv("cars-electric-comments.csv")

test_senti = []
base_word = []

for i in range(len(df)):

    if random.uniform(0.0,1.0) >= 0.5:
        test_senti.append('Good')
    else:
        test_senti.append('Bad')

    tmp_verbs = []
    word_list = df.iloc[i]['body'].split()
    for word in word_list:
        tmp_verbs.append(wnl.lemmatize(word, pos="v"))

    tmp_verbs = list(set(tmp_verbs))
    base_word.append(tmp_verbs)
    

df['test_senti'] = test_senti
df['base_word'] = base_word

df.to_csv('EV_test.csv', index=False)
