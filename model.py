from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
import pandas as pd
import numpy as np
import sys

def model():
    data = pd.read_csv("/Users/maria/Documents/telegramm_chat/new_dataset.csv")

    y = np.array(data["toxic"])
    x = np.array(data["comment"])
    xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size=0.3, random_state=42)
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('clf', SGDClassifier())
    ])

    pipeline.fit(xtrain, ytrain)
    predicted = pipeline.predict(xtest)
    print(accuracy_score(ytest, predicted))
    print(f1_score(ytest, predicted))

    while True:
        intent = input(">>> ").strip()
        intents = [intent]
        predicted = pipeline.predict(intents)
        print(predicted[0])

if __name__ == '__main__':
    sys.exit(model())