import pandas as pd
import numpy as np
import re
from tqdm import tqdm

stop_words = [line.strip() for line in open('russian_stop_word.txt', 'r')]

del_n = re.compile('\n')
clean_text = re.compile('[^а-я\s]')
del_spaces = re.compile('\s{2,}')

def prepare_text(text):
    text = del_n.sub(' ', text.lower())
    res_text = clean_text.sub('', text)
    return del_spaces.sub(' ',res_text)

def del_stopwords(text):
    text = text.split(" ")
    clean_tokens = [x if x not in stop_words else '' for x in text]
    res_text = ' '.join(clean_tokens)
    return res_text

data = pd.read_csv("/Users/maria/Documents/telegramm_chat/new_dataset.csv")
x = np.array(data["comment"])
y = np.array(data["toxic"])
clean_comment = []

for comment in tqdm(x):
    comment = comment.lower()
    comment = del_stopwords(comment)
    comment = prepare_text(comment)
    clean_comment.append(comment)

df = pd.DataFrame({'comment': clean_comment, 'toxic': y})
df.to_csv('clean_comment.csv', index=True)
