import joblib
import pandas as pd
import numpy as np
import re

stop_words = [line.strip() for line in open('russian_stop_word.txt', 'r')]
del_n = re.compile('\n')
clean_text = re.compile('[^а-яё\s]')
del_spaces = re.compile('\s{2,}')

def prepare_text(text):
    text = del_n.sub(' ', text.lower())
    res_text = clean_text.sub('', text)
    return del_spaces.sub(' ', res_text)

def del_stopwords(text):
    text = text.split(" ")
    clean_tokens = [x if x not in stop_words else '' for x in text]
    res_text = ' '.join(clean_tokens)
    return res_text

data = pd.read_csv("/Users/maria/Documents/telegramm_chat/chats.csv", sep="\t", header=None)
data = data.dropna(how='all')
new_data = [del_stopwords(str(x).lower()) for x in np.array(data)]
new_data = [prepare_text(x) for x in new_data]

model = joblib.load('model.pkl')
predictions = model.predict(new_data)

df = pd.DataFrame({'chats': new_data, 'toxic': predictions})
df.to_csv(f'prediction_chat.csv', index=False)

chat = pd.read_csv("/Users/maria/Documents/telegramm_chat/prediction_chat.csv")

comment = np.array(chat["chats"])
toxic = np.array(chat["toxic"])

toxic_comment = []
toxic = []
for i in range(len(new_data)):
    if predictions[i] == -1:
        toxic_comment.append(new_data[i])
        toxic.append(predictions[i])

df = pd.DataFrame({'chats': toxic_comment, 'toxic': toxic})
df.to_csv(f'toxic_chat.csv', index=False)









