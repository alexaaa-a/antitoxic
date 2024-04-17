
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

data = pd.read_csv("/Users/maria/Documents/telegramm_chat/dataset.csv")
dataset = data[data["normal"] == +1]["comment"].values

sentence = ""
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(dataset)
sentence_vector = vectorizer.transform([sentence])
s = cosine_similarity(sentence_vector, X).flatten()


index = np.argmax(s)


closest_sentence = dataset[index]
print(closest_sentence)

