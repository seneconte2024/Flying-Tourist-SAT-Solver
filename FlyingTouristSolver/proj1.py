import sys
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from datetime import datetime, timedelta

class City:
    def __init__(self, name, code, nights):
        self.name = name        # Name of the city
        self.code = code        # Code of the city (e.g., postal code)
        self.nights = nights      # Nights to be spent in the city
    
class Flight:
    def __init__(self, day, departure_city_name, departure_city_code,  arrival_city_name, arrival_city_code, departure_time, arrival_time, price):
        self.day = day
        self.departure_city_name = departure_city_name
        self.departure_city_code = departure_city_code
        self.arrival_city_name = arrival_city_name
        self.arrival_city_code = arrival_city_code
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.price = price
        
    def __str__(self):
        return f"{self.day} {self.departure_city_name} {self.arrival_city_name} {self.departure_time} {self.price}"


def parse_input_file():
    cities = {}  # Set to hold City objects
    X_f = {}    # variables  X_f: 1 if there is a flight from city i to city j, 0 other wise
    base_city_start_flight_vars = [] # vars of flights that start at base city
    base_city_end_flight_vars = []   # vars of flights that end at base city.
    days_of_holidays = 0 # number of days of tourist holidays.

    # Read the input from stdin
    input_data = sys.stdin.read().strip().splitlines()

    # Reading number of cities
    n = int(input_data[0])

    # Reading the base city (no nights specified)
    base_city_info = input_data[1].split()
    base_city = City(name=base_city_info[0], code=base_city_info[1], nights=0)
    cities[base_city_info[1]] = base_city

    # Reading the remaining cities
    for i in range(2, 2 + n - 1):
        city_info = input_data[i].split()
        city = City(name=city_info[0], code=city_info[1], nights=int(city_info[2]))
        cities[city_info[1]] = city
        days_of_holidays = days_of_holidays + city.nights

    # Reading the number of flights
    m = int(input_data[2 + n - 1])

    # Reading the flight information
    X_f_value = 1
    for i in range(3 + n - 1, 3 + n - 1 + m):
        flight_info = input_data[i].split()
        date = flight_info[0]
        departure_code = flight_info[1]
        arrival_code = flight_info[2]
        departure_time = flight_info[3]
        arrival_time = flight_info[4]
        cost = int(flight_info[5])

        # Append the flight object to the flights dict
        flight = Flight(day=date , departure_city_name=cities[departure_code].name, departure_city_code=departure_code, arrival_city_name=cities[arrival_code].name, arrival_city_code=arrival_code, departure_time=departure_time, arrival_time=arrival_time , price=cost)
        X_f[X_f_value] = flight

        #Append flight var into base city start or end list if base city is part of the flight
        if departure_code == base_city.code:
            base_city_start_flight_vars.append(X_f_value)
        if arrival_code == base_city.code:
            base_city_end_flight_vars.append(X_f_value)

        X_f_value = X_f_value + 1
        
    return X_f, cities, base_city, base_city_start_flight_vars, base_city_end_flight_vars, days_of_holidays

def add_days_to_date(day_str: str, n_days: int) -> str:
    # Convert input string 'DD/MM' to datetime object
    date_obj = datetime.strptime(day_str, '%d/%m')
    
    # Add the specified number of days
    new_date = date_obj + timedelta(days=n_days)
    
    # Format the new date back to 'DD/MM' string
    return new_date.strftime('%d/%m')

def print_solution(m, flights):
    minimum_flights = ''
    total_price = 0
    for var in m:
        if var in flights:
            flight = flights[var]
            minimum_flights = minimum_flights + flight.__str__() + "\n"
            total_price = total_price + flight.price

    print(total_price)
    out = minimum_flights[:-1]
    print(out)


if __name__ == "__main__":
    X_f, cities, base_city, base_city_start_flight_vars, base_city_end_flight_vars, days_of_holidays = parse_input_file()

    solver = solver = RC2(WCNF())

    # Encoding Base City departure flight Constraints
    one_of_departures = []
    for i in range(len(base_city_start_flight_vars)):
        one_of_departures.append(base_city_start_flight_vars[i])
        for j in range(i + 1, len(base_city_start_flight_vars)):
                solver.add_clause([-base_city_start_flight_vars[i], -base_city_start_flight_vars[j]])
    solver.add_clause(one_of_departures)

    # Encoding Base City arrival flight Constraints
    one_of_arrivals = []
    for i in range(len(base_city_end_flight_vars)):
        one_of_arrivals.append(base_city_end_flight_vars[i])
        for j in range(i + 1, len(base_city_end_flight_vars)):
                solver.add_clause([-base_city_end_flight_vars[i], -base_city_end_flight_vars[j]])
    solver.add_clause(one_of_arrivals)

    # Encoding the flight must start at base city and end in base city after n days of holidays.
    for base_city_departure_var in base_city_start_flight_vars:
        arrival_day_vars = []

        flight_day = X_f[base_city_departure_var].day  # Format: DD/MM
        
        arrival_day = add_days_to_date(flight_day, days_of_holidays)

        for base_city_arrival_var in base_city_end_flight_vars:
            arrival_flight = X_f[base_city_arrival_var]
            if arrival_flight.day == arrival_day:
                arrival_day_vars.append(base_city_arrival_var)
        arrival_day_vars.insert(0, -base_city_departure_var)
        solver.add_clause(arrival_day_vars)  
    
    # Tour Sequence Constraints: Ensure that the tourist visits each city exactly once (except for the base city)
    # The tourist can only leave each city once and arrive at each city once, ensuring a continuous trip.
    for outer_flight_key in X_f:
        outer_flight = X_f[outer_flight_key]

        if outer_flight.departure_city_code == base_city.code:
            continue

        for inner_flight_key in X_f:
            inner_flight = X_f[inner_flight_key]
            if inner_flight_key > outer_flight_key:
                if inner_flight.departure_city_code == outer_flight.departure_city_code:
                    solver.add_clause([-outer_flight_key, -inner_flight_key])
                    
    for outer_flight_key in X_f:
        outer_flight = X_f[outer_flight_key]

        if outer_flight.arrival_city_code == base_city.code:
            continue

        for inner_flight_key in X_f:
            inner_flight = X_f[inner_flight_key]
            if inner_flight_key > outer_flight_key:
                if inner_flight.arrival_city_code == outer_flight.arrival_city_code:
                    solver.add_clause([-outer_flight_key, -inner_flight_key])
            
    # City Visit Constraints: Ensure that the tourist stays the correct number of nights in each city:
    # This ensures that the tourist fulfills their planned stay in each city.
    for outer_flight_key in X_f:
        outer_flight = X_f[outer_flight_key]
        arrival_city_code = X_f[outer_flight_key].arrival_city_code

        if arrival_city_code == base_city.code:
            continue

        day = outer_flight.day  # Format: DD/MM
        nights_in_city = cities[arrival_city_code].nights
    
        new_departure_day = add_days_to_date(day, nights_in_city)
        X_f_tourist_can_take = []
        for inner_flight_key in X_f:
            inner_flight = X_f[inner_flight_key]
            if inner_flight.departure_city_code == arrival_city_code and new_departure_day == inner_flight.day:
                X_f_tourist_can_take.append(inner_flight_key) 
        
        # if the tourist is in city c on day d than he/she can take any flight in the list of X_f_tourist_can_take.
        # Remember, tourist cannot take 2 or more flight in the same city.
        X_f_tourist_can_take.insert(0, -outer_flight_key)
        solver.add_clause(X_f_tourist_can_take) 

    # Encode Soft clause: weight is the price of the flight
    for flight_key in X_f:
        flight = X_f[flight_key]
        solver.add_clause([-flight_key], weight=flight.price)

    m = solver.compute()
    print_solution(m, X_f)
    