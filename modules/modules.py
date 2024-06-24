import os
import requests
import boto3
import json
from flask import render_template, jsonify
from datetime import datetime, timedelta
from googletrans import Translator

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name = 'eu-central-1')
rec_data = {}


def get_weather_data(inp):
    """
    This function recieves weather data from API
        Params: inp - user's input.
        Return: data in json format.
    """

    key = 'ADD5Z55GB8EXEABMJW7EWQAX9'
    today = datetime.today().date()
    end_date = (datetime.today() + timedelta(days=7)).date()
    api = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{inp}/{today}/{end_date}?unitGroup=uk&key={key}&contentType=json'

    try:
        with requests.get(api) as data:
            global rec_data
            rec_data = data.json()
            return data.json()
    except requests.exceptions.RequestException:
        return None
    except ValueError as err:
        return None
     
def get_weekend_days(data):
    """
    This function translates data format from 'YYYY-MM-DD' to weekday name
        Params: data - dates from API.
        Return: dates - converted dates.
    """
    dates = data.get('days')
    dates = list(map(lambda x: dates[x].get('datetime'), range(7)))
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates[:7]]
    dates = [d.strftime("%A") for d in dates[:7]]
    return dates

def translate_place(data):
    """
    This function translates country's name from its language to english language
        Params: data - conrty to translate to english.
        Return: translated country.
    """
    translator = Translator()
    place = data.get('resolvedAddress')
    return translator.translate(place).text

def print_data(name):
    """
    This function validates user's input, if true -> makes API call to recive data from the server
    and passes it to index.html. if false -> renders index.html with specific error
        Params: name - user's input.
        Return: render_template.
    """
    if (name.replace(" ","").isalpha() and len(name) <= 15):
        data = get_weather_data(name)
        error = None
        dates = None
        place = None
        if data:
            dates = get_weekend_days(data)
            place = translate_place(data)
        else:
            error = "400 Bad request"
        return render_template('index.html', data=data, error=error, dates=dates, place=place)
    else:
        error = "Invalid Input"
    return render_template('index.html', error=error)

def download_image():
    bucket_name = 'denisbacket1'
    object_key = 'weather_app_pic/sky.jpeg'
    desktop_path = os.path.join(os.path.expanduser('~'))
    local_file_path = '/home/ec2-user/sky.jpeg'

    try:
        s3.download_file(bucket_name, object_key, '/home/ec2-user/sky.jpeg')
        return local_file_path 
    except Exception as e:
        print(str(e))


def record_to_db():
    table_name = 'weather_app_records'
    table = dynamodb.Table(table_name)
    data = rec_data
    days = data.get('days', [])
    response = ''

    # Iterate over days and extract desired information
    for day in days:
        datetime = day.get('datetime')
        tempmax = day.get('tempmax')
        tempmin = day.get('tempmin')
        humidity = day.get('humidity')
        # Prepare the item to be stored in DynamoDB
        item = {
            'resolvedAddress': data.get('resolvedAddress'),
            'datetime': datetime + ' tempmax: ' + str(tempmax) + ' tempmin: ' + str(tempmin) + ' humidity: ' + str(humidity)
        }

        try:
            response = table.put_item(Item=item)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Data stored successfully", "response": response})

def get_user_history_file(email):
    filename = f"{email}_search_history.json"
    return os.path.join('user_histories', filename)

def initialize_history_file(email):

    if not os.path.exists('user_histories'):
        os.makedirs('user_histories')
    
    history_file = get_user_history_file(email)
    if not os.path.exists(history_file) or os.stat(history_file).st_size == 0:
        with open(history_file, 'w') as file:
            json.dump([], file)

def save_search_history(email, city):
    initialize_history_file(email)

    date = datetime.today().date().isoformat()
    new_entry = {'date': date, 'city': city}
    
    history_file = get_user_history_file(email)
    
    try:
        with open(history_file, 'r+') as file:
            history = json.load(file)
            history.append(new_entry)
            file.seek(0)
            json.dump(history, file, indent=4)
    except json.JSONDecodeError:
        with open(history_file, 'w') as file:
            json.dump([new_entry], file, indent=4)


    
