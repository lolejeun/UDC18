import pickle
import numpy as np
import math
from sklearn.linear_model import LinearRegression

score_weight = 0.015
price_weight = 0
distance_weight = 0.121
intercept = -0.581

pickle_in = open('Recommend.pickle', 'rb')
classifier = pickle.load(pickle_in)

X = []
y = []
dataset = np.load('Data.npy')
for data in dataset:
    X.append(data[0])
    y.append(data[1])

def recommend(user_location_x, user_location_y, user_money):
    input_data = [user_location_x, user_location_y, user_money]
    destinations = classifier.kneighbors(np.array(input_data).reshape(1, -1), n_neighbors=10, return_distance=False)

    recommendation = {}
    for destination in destinations[0]:
        destination_x, destination_y = X[destination][:2]
        distance = math.sqrt(abs(user_location_x - float(destination_x))**2 + abs(user_location_y - float(destination_y))**2)
        score_price_distance = y[destination][1] * score_weight + X[destination][2] * price_weight + distance * distance_weight + intercept + 20
        recommendation[score_price_distance] = [y[destination][0], y[destination][1], destination_x, destination_y, X[destination][2], distance]

    sorted_recommendation = []
    for key in reversed(sorted(recommendation.keys())):
        sorted_recommendation.append([key, recommendation[key]])

    return sorted_recommendation

def weights(choice, recommendations):
    global score_weight, price_weight, distance_weight, intercept
    X = []
    y = [0] * len(recommendations)

    for data in recommendations:
        X.append([data[1][1], int(data[1][4]), round(data[1][5] * 10066.783078052693) / 100])
    y[choice - 1] = 1

    classifier = LinearRegression()
    classifier.fit(X, y)
    score_weight, price_weight, distance_weight = classifier.coef_
    intercept = classifier.intercept_

while True:
    count = 1

    destinations = recommend(float(input('Your Latitude: ')), float(input('Your Longitude: ')), int(input('Amount of Money: ')))
    for place in destinations:
        print('\n{}.'.format(count), place[1][0])
        print('Worth Value: ', round(place[0] * 100) / 100)
        print('Score: ', place[1][1])
        print('Price: ', int(place[1][4]))
        print('Distance: ', round(place[1][5] * 10066.783078052693) / 100, 'KM\n')

        count += 1

    user_choice = int(input('Your Favorite: '))
    weights(user_choice, destinations)
    print()
