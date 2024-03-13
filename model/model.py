from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import pandas as pd
import numpy as np
import joblib


data = pd.read_csv("/Users/maria/Documents/telegramm_chat/dataset.csv")
x = np.array(data["comment"])
y = np.array(data["normal"])

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', SGDClassifier(loss='hinge'))
])
pipeline.fit(x_train, y_train)
joblib.dump(pipeline, 'model.pkl')

predicted = pipeline.predict(x_test)

precision = precision_score(y_test, predicted)
recall = recall_score(y_test, predicted)
print(f"Accuracy: {accuracy_score(y_test, predicted)}") #Accuracy: 0.9093264596506773
print(f"F1_score:{f1_score(y_test, predicted)}")        #F1_score:0.9474576798605925
print(f'Precision: {precision}')                       #Precision: 0.9014136629413071
print(f'Recall: {recall}')                             #Recall: 0.998458738461034




