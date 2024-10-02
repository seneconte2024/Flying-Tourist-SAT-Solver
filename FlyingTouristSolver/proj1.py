import sys
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from datetime import datetime, timedelta

class City:
    def __init__(self, name, code, nights, variable):
        self.name = name        # Name of the city
        self.code = code        # Code of the city (e.g., postal code)
        self.nights = nights      # Nights to be spent in the city
        self.variable = variable  # Literal representation or description of the city

    def __str__(self):
        return f"City(Name: {self.name}, Code: {self.code}, Nights: {self.nights}, Variable: {self.variable})"

    def get_details(self):
        return {
            "name": self.name,
            "code": self.code,
            "nights": self.nights,
            "variable": self.variable
        }
    
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
    flights_variables = {}    # variables  X_(i,j) - 1 if there is a flight from city i to city j
    city_visit_variables = {} # variables Y_(c, d) - 1 if tourist is visiting city c on day d - 0 
    base_city_start_flight_vars = [] # vars of flights that start at base city
    base_city_end_flight_vars = []   # vars of flights that end at base city.
    days_of_holidays = 0 # number of days of tourist holidays.

    # Read the input from stdin
    input_data = sys.stdin.read().strip().splitlines()

    # Reading number of cities
    n = int(input_data[0])

    # Reading the base city (no nights specified)
    city_var = 1
    base_city_info = input_data[1].split()
    base_city = City(name=base_city_info[0], code=base_city_info[1], nights=0, variable=city_var)
    cities[base_city_info[1]] = base_city
    city_var = city_var + 1

    # Reading the remaining cities
    for i in range(2, 2 + n - 1):
        city_info = input_data[i].split()
        city = City(name=city_info[0], code=city_info[1], nights=int(city_info[2]), variable=city_var)
        cities[city_info[1]] = city
        city_var = city_var + 1
        days_of_holidays = days_of_holidays + city.nights

    # Reading the number of flights
    m = int(input_data[2 + n - 1])

    # Reading the flight information
    flights_variables_value = n + 1
    city_visit_variables_value = m + 1
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
        flights_variables[flights_variables_value] = flight

        #Append flight var into base city start or end list if base city is part of the flight
        if departure_code == base_city.code:
            base_city_start_flight_vars.append(flights_variables_value)
        if arrival_code == base_city.code:
            base_city_end_flight_vars.append(flights_variables_value)

        flights_variables_value = flights_variables_value + 1
        
        # Append the departure city into cities visited dict
        city_visit_variables[(departure_code, date)] = city_visit_variables_value
        city_visit_variables_value = city_visit_variables_value + 1

        # Append the arrival city into cities visited dict
        city_visit_variables[(arrival_code, date)] = city_visit_variables_value
        city_visit_variables_value = city_visit_variables_value + 1

    return flights_variables, city_visit_variables, cities, base_city, base_city_start_flight_vars, base_city_end_flight_vars, days_of_holidays

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
    flights, city_visit_variables, cities, base_city, base_city_start_flight_vars, base_city_end_flight_vars, days_of_holidays = parse_input_file()

    solver = solver = RC2(WCNF())

    # Every city must be visited
    for city_key in cities:
        solver.add_clause([cities[city_key].variable])
        #print([cities[city_key].variable]) 

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

        flight_day = flights[base_city_departure_var].day  # Format: DD/MM
        days_to_add = days_of_holidays
        # Parse the input date string into a datetime object (assuming the year is not important, default to 1900)
        date_obj = datetime.strptime(flight_day, "%d/%m")

        # Add the specified number of days using timedelta
        new_date_obj = date_obj + timedelta(days=days_to_add)

        # Format the new date back into the desired 'DD/MM' format
        arrival_day = new_date_obj.strftime("%d/%m")

        for base_city_arrival_var in base_city_end_flight_vars:
            arrival_flight = flights[base_city_arrival_var]
            if arrival_flight.day == arrival_day:
                arrival_day_vars.append(base_city_arrival_var)
        arrival_day_vars.insert(0, -base_city_departure_var)
        solver.add_clause(arrival_day_vars)
        #print(arrival_day_vars)

    # Encoding Flight Schedule Constraints: Ensure that if a flight 𝑓
    #is selected, the tourist must be in the departure city on the day of departure and in the arrival city on the day of arrival
    tourist_is_in_city_on_day = []
    for flight_key in flights:
        flight = flights[flight_key]
        departure_city_on_day = (flight.departure_city_code, flight.day)
        departure_city_on_day_var = city_visit_variables[departure_city_on_day]
        arrival_city_on_day = (flight.arrival_city_code, flight.day)
        arrival_city_on_day_var = city_visit_variables[arrival_city_on_day]
        
        #if flight is selected than tourist is in departure city on the day of flight 
        #solver.add_clause([-flight_key, departure_city_on_day_var])
        #if flight is selected than tourist is in arrival city on the day of flight
        solver.add_clause([-flight_key, arrival_city_on_day_var])
        # the tourist is in one of the city in each day
        #tourist_is_in_city_on_day.append(departure_city_on_day_var)
        tourist_is_in_city_on_day.append(arrival_city_on_day_var)
    solver.add_clause(tourist_is_in_city_on_day)
        
    
    # Tour Sequence Constraints: Ensure that the tourist visits each city exactly once (except for the base city)
    # The tourist can only leave each city once and arrive at each city once, ensuring a continuous trip.
    cities_already_processed = set()
    for outer_flight_key in flights:
        outer_flight = flights[outer_flight_key]
        if outer_flight.departure_city_code != base_city.code:
            one_of_flights_must_be_taken = [outer_flight_key]
            for inner_flight_key in flights:
                inner_flight = flights[inner_flight_key]
                if inner_flight_key > outer_flight_key:
                    if inner_flight.departure_city_code == outer_flight.departure_city_code:
                        solver.add_clause([-outer_flight_key, -inner_flight_key])
                        one_of_flights_must_be_taken.append(inner_flight_key)

            if outer_flight.departure_city_code not in cities_already_processed:
                solver.add_clause(one_of_flights_must_be_taken)
                cities_already_processed.add(outer_flight.departure_city_code)
                #print(one_of_flights_must_be_taken)

    cities_already_processed_arrival = set()
    for outer_flight_key in flights:
        outer_flight = flights[outer_flight_key]
        if outer_flight.arrival_city_code != base_city.code:
            one_of_flights_must_be_taken = [outer_flight_key]
            for inner_flight_key in flights:
                inner_flight = flights[inner_flight_key]
                if inner_flight_key > outer_flight_key:
                    if inner_flight.arrival_city_code == outer_flight.arrival_city_code:
                        solver.add_clause([-outer_flight_key, -inner_flight_key])
                        one_of_flights_must_be_taken.append(inner_flight_key)

            if outer_flight.arrival_city_code not in cities_already_processed_arrival:
                solver.add_clause(one_of_flights_must_be_taken)
                cities_already_processed_arrival.add(outer_flight.arrival_city_code)
                #print(one_of_flights_must_be_taken)

    
    # City Visit Constraints: Ensure that the tourist stays the correct number of nights in each city:
    # This ensures that the tourist fulfills their planned stay in each city.
    for outer_flight_key in flights:
        outer_flight = flights[outer_flight_key]
        arrival_city_code = flights[outer_flight_key].arrival_city_code

        if arrival_city_code == base_city.code:
            continue

        day = outer_flight.day  # Format: DD/MM
        days_to_add = cities[arrival_city_code].nights
        # Parse the input date string into a datetime object (assuming the year is not important, default to 1900)
        date_obj = datetime.strptime(day, "%d/%m")

        # Add the specified number of days using timedelta
        new_date_obj = date_obj + timedelta(days=days_to_add)

        # Format the new date back into the desired 'DD/MM' format
        new_departure_day = new_date_obj.strftime("%d/%m")
        flights_tourist_can_take = []
        for inner_flight_key in flights:
            inner_flight = flights[inner_flight_key]
            if inner_flight.departure_city_code == arrival_city_code and new_departure_day == inner_flight.day:
                flights_tourist_can_take.append(inner_flight_key) 
        
        # if the tourist is in city c on day d than he/she can take any flight in the list of flights_tourist_can_take.
        # Remember, tourist cannot take 2 or more flight in the same city.
        if len(flights_tourist_can_take) > 0:
            flights_tourist_can_take.insert(0, -outer_flight_key)
            solver.add_clause(flights_tourist_can_take) 


    # Encode Soft clause: weight is the price of the flight
    for flight_key in flights:
        flight = flights[flight_key]
        solver.add_clause([-flight_key], weight=flight.price)

    m = solver.compute()
    print_solution(m, flights)
    