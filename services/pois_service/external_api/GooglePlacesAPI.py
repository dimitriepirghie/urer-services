import requests
import json
from datetime import datetime

__author__ = "Dimitrie Pirghie"


allowed_return_types = ['xml', 'json']

mandatory_search_parameters = ['location', 'radius', 'output']
allowed_search_parameters = ['keyword', 'language', 'minprice',
                             'maxprice', 'name', 'opennow', 'type'] + mandatory_search_parameters


favourite_types = ['airport', 'cafe', 'church', 'restaurant', 'pharmacy',
                   'museum', 'night_club', 'library', 'shopping_mall',
                   'travel_agency', 'university', 'hair_care', 'gym', 'park', 'spa', 'florist', 'car_rental',
                   'campground', 'bowling_alley', 'book_store', 'bar']


class GooglePlacesAPI(object):
    """

    """
    def __init__(self, api_key=None):
        """

        :param api_key:
        """
        if api_key:
            self.api_key = api_key
        else:
            raise ValueError("Invalid API Key")

    def search(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        request_url_format = "https://maps.googleapis.com/maps/api/place/nearbysearch/{}?{}"
        # Default value for output parameter is json
        if 'output' not in kwargs:
            kwargs['output'] = 'json'

        sanitize_parameters_functions = [unicode, unicode.lower, unicode.strip]
        parameters = kwargs.keys()

        for sanitize_func in sanitize_parameters_functions:
            parameters = map(sanitize_func, parameters)

        if 'radius' not in kwargs:
            print('Radius not in request set default to 500')
            parameters.append('radius')
            kwargs['radius'] = 500

        mandatory_missing = set(mandatory_search_parameters) - set(parameters)
        if mandatory_missing:
            raise ValueError("Mandatory parameters missing " + str(mandatory_missing))

        invalid_parameters = set(parameters) - set(allowed_search_parameters)
        if invalid_parameters:
            raise ValueError("Invalid parameters " + str(invalid_parameters))

        output_type = kwargs['output']
        if output_type.lower() not in allowed_return_types:
            raise ValueError('Invalid output type')

        del kwargs['output']
        parameters.remove('output')

        # Build parameters
        parameter_format = "{}={}"
        parameters_values_list = [parameter_format.format("key", self.api_key)]
        for param_name in parameters:
            parameters_values_list.append(parameter_format.format(param_name, kwargs[param_name]))

        parameters_string_request = "&".join(parameters_values_list)
        request_url = request_url_format.format(output_type, parameters_string_request)

        try:
            request_result = requests.get(request_url)
            results_json = json.loads(request_result.text)

            results_to_client = []

            if 'OK' not in results_json['status']:
                print('[ERROR] - ' + str(results_json['status']))
                return None

            for place in results_json['results']:
                dict_ = {'place_id': place['place_id'], 'output': 'json'}

                place_details = self.place_details(**dict_)
                place_client_dict = {}
                place_details_json = json.loads(place_details)

                if 'OK' in place_details_json['status']:
                    place_details_json = place_details_json['result']

                    places_types = set(place_details_json['types'])
                    favourite_types_set = set(favourite_types)
                    if not places_types.intersection(favourite_types_set):
                        continue

                    place_client_dict['title'] = place_details_json.pop('name') if 'name' in place_details_json else 'Undefined'
                    place_client_dict['image'] = place_details_json.pop('icon') if 'icon' in place_details_json else 'Undefined'
                    place_client_dict['from'] = 'Google Maps'
                    place_client_dict['link'] = place_details_json.pop('website') if 'website' in place_details_json else 'Undefined'
                    place_client_dict['map'] = place_details_json.pop('url') if 'url' in place_details_json else 'Undefined'
                    place_client_dict['time'] = datetime.utcnow().strftime('%b %d %Y %H:%M:%S')
                    place_client_dict['description'] = 'ToDO Search for description'
                    results_to_client.append(place_client_dict)
                else:
                    place_client_dict['title'] = place.pop(
                        'name') if 'name' in place else 'Undefined'
                    place_client_dict['image'] = place.pop(
                        'icon') if 'icon' in place else 'Undefined'
                    place_client_dict['from'] = 'Google Maps'
                    place_client_dict['link'] = '#'
                    place_client_dict['map'] = '#'
                    place_client_dict['time'] = datetime.utcnow().strftime('%b %d %Y %H:%M:%S')
                    place_client_dict['description'] = 'ToDO Search for description'
                    results_to_client.append(place_client_dict)

            print("Found " + str(len(results_to_client)) + " results")
            if 200 == request_result.status_code and len(results_to_client) > 0:
                # print(str(results_to_client))
                return json.dumps(results_to_client)
            else:
                print("Google returned code different from 200")
                return None
        except Exception as e:
            print("Exception")
            print(e)
            print("[ERROR] - " + e.message + ' of type ' + str(type(e)))
            return None

    def place_details(self, *args, **kwargs):

        sanitize_parameters_functions = [str.lower, str.strip]
        parameters = kwargs.keys()

        for sanitize_func in sanitize_parameters_functions:
            parameters = map(sanitize_func, parameters)

        output_type = kwargs['output']
        if output_type.lower() not in allowed_return_types:
            raise ValueError('Invalid output type')

        del kwargs['output']
        parameters.remove('output')

        if len(parameters) != 1 and not 'placeid' not in parameters:
            raise ValueError('Invalid parameters')

        parameter_format = "{}={}"
        parameters_values_list = [parameter_format.format("key", self.api_key)]
        request_url_format = "https://maps.googleapis.com/maps/api/place/details/{}?{}"

        for param_name in parameters:
            parameters_values_list.append(parameter_format.format(param_name, kwargs[param_name]))

        parameters_string_request = "&".join(parameters_values_list)

        request_url = request_url_format.format(output_type, parameters_string_request)

        try:
            request_result = requests.get(request_url)
            if 200 == request_result.status_code:
                return request_result.text
            else:
                return None
        except Exception as e:
            print e.message
            return None

    def place_image(self, *args, **kwargs):

        sanitize_parameters_functions = [str.lower, str.strip]
        parameters = kwargs.keys()

        for sanitize_func in sanitize_parameters_functions:
            parameters = map(sanitize_func, parameters)

        if len(parameters) != 2 and not 'photo_reference' not in parameters:
            raise ValueError('Invalid parameters')

        if len(parameters) != 2 and not 'maxheight' not in parameters:
            raise ValueError('Invalid parameters')

        parameter_format = "{}={}"
        parameters_values_list = [parameter_format.format("key", self.api_key)]
        request_url_format = "https://maps.googleapis.com/maps/api/place/photo?{}"

        for param_name in parameters:
            parameters_values_list.append(parameter_format.format(param_name, kwargs[param_name]))

        parameters_string_request = "&".join(parameters_values_list)

        request_url = request_url_format.format(parameters_string_request)

        try:
            request_result = requests.get(request_url, stream=True)
            if 200 == request_result.status_code:
                with open('/home/ullr/Desktop/image.png', 'wb+') as h:
                    h.write(request_result.content)
                h.close()

                return request_result.content
            else:
                return None
        except Exception as e:
            print e.message
            return None