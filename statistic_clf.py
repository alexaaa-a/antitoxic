import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import BernoulliNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score

data = pd.read_csv("/Users/maria/Documents/telegramm_chat/labeled.csv")
data = data[["comment", "toxic"]]
x = np.array(data["comment"])
y = np.array(data["toxic"])

classifiers = [
    KNeighborsClassifier(5),
    SVC(),
    DecisionTreeClassifier(),
    RandomForestClassifier(),
    BernoulliNB(),
    LogisticRegression(),
]
log_cols = ["Classifier", "Accuracy"]
log = pd.DataFrame(columns=log_cols)

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
acc_dict = {}
score_dict = {}

for clf in classifiers:
    name = clf.__class__.__name__
    model = Pipeline([('tfidf', TfidfVectorizer()),
                      ('clf', clf)])
    model.fit(x_train, y_train)
    train_predictions = model.predict(x_test)

    acc = accuracy_score(y_test, train_predictions)

    if name in acc_dict:
        acc_dict[name] += acc
    else:
        acc_dict[name] = acc

    score = f1_score(y_test, train_predictions)

    if name in score_dict:
        score_dict[name] += score
    else:
        score_dict[name] = score

sns.barplot(x=acc_dict.values(), y=acc_dict.keys(), label="Accuracy", color="green")
plt.xlabel('Accuracy')
plt.ylabel('Classifier')

sns.barplot(x=score_dict.values(), y=score_dict.keys(), label="Score")
plt.xlabel('Score')
plt.ylabel('Classifier')
plt.show()



