from flask import Flask, render_template, request, jsonify
import numpy as np
import random
import requests
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

# ACO parameters (default values)
N = 50  # Number of ants
T = 100  # Number of iterations
alpha = 1.0  # Pheromone importance
beta = 2.0  # Heuristic importance
rho = 0.5  # Evaporation rate
Q = 100  # Pheromone deposit

# Your API keys
openweathermap_api_key = 'ef16aec95335978903143560c0af85ef'
aviationstack_api_key = '4970ec9c0caf33db5b6670a82bc858ae'

# Function to fetch weather data
def fetch_weather_data(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=hourly,daily&appid={api_key}"
    response = requests.get(url)
    return response.json()

# Function to fetch flight data from AviationStack
def fetch_flight_data_aviationstack(api_key, source_code, destination_code):
    url = f"http://api.aviationstack.com/v1/flights?access_key={api_key}&dep_iata={source_code}&arr_iata={destination_code}"
    response = requests.get(url)
    return response.json()

# Normalize data
def normalize(df, columns):
    scaler = MinMaxScaler()
    df[columns] = scaler.fit_transform(df[columns])
    return df

# Calculate composite risk factor
def calculate_composite_risk(weather_df, flight_df):
    merged_df = weather_df.merge(flight_df, left_index=True, right_index=True)
    merged_df['composite_risk'] = (merged_df['temp'] + merged_df['humidity'] +
                                   merged_df['wind_speed'] + merged_df['num_flights']) / 4
    return merged_df['composite_risk'].values

# ACO algorithm implementation
def ant_colony_optimization(num_nodes, distances, risks, pheromones, heuristics, N, T, alpha, beta, rho, Q):
    best_route = None
    best_cost = float('inf')

    for t in range(T):
        all_routes = []
        all_costs = []

        for _ in range(N):
            route = []
            visited = set()
            current_node = random.randint(0, num_nodes - 1)
            route.append(current_node)
            visited.add(current_node)

            while len(visited) < num_nodes:
                probabilities = []
                for next_node in range(num_nodes):
                    if next_node not in visited:
                        probability = (pheromones[current_node][next_node] ** alpha) * \
                                      (heuristics[current_node][next_node] ** beta)
                        probabilities.append((next_node, probability))
                total_prob = sum(p for _, p in probabilities)
                probabilities = [(node, p / total_prob) for node, p in probabilities]

                next_node = random.choices([node for node, _ in probabilities],
                                           weights=[p for _, p in probabilities])[0]
                route.append(next_node)
                visited.add(next_node)
                current_node = next_node

            route_cost = calculate_route_cost(route, distances, risks)
            all_routes.append(route)
            all_costs.append(route_cost)

            if route_cost < best_cost:
                best_route = route
                best_cost = route_cost

        # Evaporate pheromones
        pheromones *= (1 - rho)

        # Deposit new pheromones
        for route, cost in zip(all_routes, all_costs):
            for i in range(len(route) - 1):
                pheromones[route[i]][route[i + 1]] += Q / cost

    return best_route, best_cost

# Calculate route cost considering both distance and composite risk
def calculate_route_cost(route, distances, risks):
    cost = 0
    for i in range(len(route) - 1):
        cost += distances[route[i]][route[i + 1]] + risks[route[i]][route[i + 1]]
    return cost

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    source_code = request.form['source_code']
    destination_code = request.form['destination_code']
    num_nodes = int(request.form['num_nodes'])
    iterations = int(request.form['iterations'])

    # Fetch flight data
    flight_data = fetch_flight_data_aviationstack(aviationstack_api_key, source_code, destination_code)

    # Example distances (replace with actual distances)
    distances = np.random.randint(100, 1000, size=(num_nodes, num_nodes))
    np.fill_diagonal(distances, 0)

    # Example composite risk calculation (replace with actual composite risk data)
    composite_risk = np.random.rand(num_nodes, num_nodes)
    np.fill_diagonal(composite_risk, 0)

    pheromones = np.ones((num_nodes, num_nodes)) / num_nodes
    heuristics = 1 / (distances + 1e-10)

    best_route, best_cost = ant_colony_optimization(num_nodes, distances, composite_risk, pheromones, heuristics, N, iterations, alpha, beta, rho, Q)

    result = {
        'best_route': best_route,
        'best_cost': best_cost
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
