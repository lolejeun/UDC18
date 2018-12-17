import csv
import numpy as np
from sklearn import neighbors
import pickle

X = []
y = []

with open('df_final.csv', encoding='utf8') as file:
    data = csv.reader(file, delimiter='\t')
    for row in data:
        if row[0] != '':
            try:
                destination_x, destination_y = float(row[2]), float(row[3])

                X.append([destination_x, destination_y, float(row[5])])
                y.append([row[4], int(row[6])])
            except ValueError:
                y.append([row[4], 0.01])

data = []
for i in range(len(X)):
    data.append([X[i], y[i]])

np.save('Data.npy', data)

classifier = neighbors.NearestNeighbors()
classifier.fit(X, y)

with open('Recommend.pickle', 'wb') as file:
    pickle.dump(classifier, file)
