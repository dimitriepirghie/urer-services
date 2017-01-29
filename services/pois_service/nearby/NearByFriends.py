from __future__ import print_function
from __future__ import print_function
import redis
import os
import time
import json
from haversine import haversine
import requests
import urlparse

# user location timeout in seconds
try:
    user_location_timeout = int(os.environ.get('location_timeout', 7200))
except ValueError:
    user_location_timeout = 7200

# Location nearby search in km
try:
    location_search_radius = int(os.environ.get('location_search_radius', 5))
except ValueError:
    location_search_radius = 5  #


class NearByFriends(object):
    @staticmethod
    def validate_request_dictionary(request_dict):
        mandatory_parameters = ['user_id', 'location', 'response_at', 'timestamp']
        parameters = request_dict.keys()
        invalid_parameters = set(mandatory_parameters) - set(parameters)
        if invalid_parameters:
            raise ValueError('Invalid Parameters ' + str(invalid_parameters))

        # Parameters are valid
        return True

    @staticmethod
    def get_redis_handler():
        url = urlparse.urlparse(os.environ.get('REDIS_URL', 'redis://localhost'))
        redis_host = url.hostname
        redis_port = url.port
        redis_password = url.password

        h_redis = redis.Redis(host=redis_host,
                              port=redis_port,
                              password=redis_password)

        try:
            print('[redis] - try ping')
            h_redis.ping()
        except redis.ConnectionError:
            print('[redis] - ping failed')
            return None
        return h_redis

    def insert_new_location(self, user_data):
        """

        :param user_data:
        :return:
        """
        epoch_time = int(time.time())
        redis_h = self.redis_handler
        user_id = user_data['user_id']
        all_keys = redis_h.keys()

        user_id_keys = filter(lambda user_key: user_id in user_key, all_keys)
        another_keys = filter(lambda user_key: user_id not in user_key, all_keys)

        # Update user keys, should be one, str((user_id, epoch_time))
        if user_id_keys:
            for uuid_key in user_id_keys:
                old_user_data = redis_h.get(uuid_key)
                # Delete old key time stamp
                redis_h.delete(uuid_key)

        # Should merge old data from redis with new data
        redis_h.set(str(user_id + ',' + str(epoch_time)), json.dumps(user_data))

        # Remove expired keys
        if another_keys:
            for uuid_key in another_keys:
                uuid, key_epoch_time = uuid_key.split(",")
                key_epoch_time = int(key_epoch_time)

                if epoch_time - key_epoch_time > user_location_timeout:
                    redis_h.delete(uuid_key)

    def __init__(self, request_dictionary):
        # JSON Request example
        """
        {
            "user_id": "1322aa",
            "response_at": "http://urer-client.herokuapp.com/receive/nearbyfriends",
            "location": "47.171571, 27.574983",
            "timestamp": 12313132 # Unix epoch time
        }
        """
        NearByFriends.validate_request_dictionary(request_dictionary)
        self.redis_handler = NearByFriends.get_redis_handler()

        self.insert_new_location(request_dictionary)
        self.find_nearby()

    @staticmethod
    def check_valid_distance(coord_1_str, coord_2_str):
        lat_1, lon_1 = map(float, coord_1_str.split(","))
        lat_2, lon_2 = map(float, coord_2_str.split(","))

        distance_in_km = haversine((lat_1, lon_1), (lat_2, lon_2))
        if distance_in_km <= location_search_radius:
            return True, distance_in_km

        return False

    def notify_users(self, user_key_1, user_key_2, distance):
        redis_h = self.get_redis_handler()
        user_1_data = json.loads(redis_h.get(user_key_1))
        user_2_data = json.loads(redis_h.get(user_key_2))

        user_id_1 = user_key_1.split(',')[0]
        user_id_2 = user_key_2.split(',')[0]

        notify_user_1 = True
        notify_user_2 = True

        if 'notify_sent_to' not in user_1_data:
            user_1_data['notify_sent_to'] = [user_key_2]
        else:
            if user_key_2 in user_1_data['notify_sent_to']:
                notify_user_1 = False
            else:
                user_1_data['notify_sent_to'].append(user_key_2)

        if 'notify_sent_to' not in user_2_data:
            user_2_data['notify_sent_to'] = [user_key_1]
        else:
            if user_key_1 in user_2_data['notify_sent_to']:
                notify_user_2 = False
            else:
                user_2_data['notify_sent_to'].append(user_key_1)

        if notify_user_1:
            friend_data = {'user_id': user_id_2, 'location': user_2_data['location'],
                           'timestamp': user_2_data['timestamp']}
            response_data = {'user_id': user_id_1, 'friends': [friend_data], 'distance': distance, 'distance_unit': 'km'}

            response_at = user_1_data['response_at']

            post_reply = requests.post(response_at, data=json.dumps(response_data),
                                       headers={'Content-type': 'application/json'})
            if 200 == post_reply.status_code:
                print('Push location for user 1 ok')
            else:
                print('Push location for user 1 not ok')

        if notify_user_2:
            friend_data = {'user_id': user_id_1, 'location': user_1_data['location'],
                           'timestamp': user_1_data['timestamp']}
            response_data = {'user_id': user_id_2, 'friends': [friend_data], 'distance': distance, 'distance_unit': 'km'}

            response_at = user_2_data['response_at']

            post_reply = requests.post(response_at, data=json.dumps(response_data),
                                       headers={'Content-type': 'application/json'})
            if 200 == post_reply.status_code:
                print('Push location for user 2 ok')
            else:
                print('Push location for user 2 not ok')

    def find_nearby(self):
        user_keys = self.redis_handler.keys()
        for i, user_key_1 in enumerate(user_keys):
            for j, user_key_2 in enumerate(user_keys):
                if i >= j:
                    continue
                location_1 = self.redis_handler.get(user_key_1)
                location_1 = json.loads(location_1)['location']
                location_2 = self.redis_handler.get(user_key_2)
                location_2 = json.loads(location_2)['location']
                print("Coords 1, " + str(location_1))
                print("Coords 2, " + str(location_2))

                distance_data = NearByFriends.check_valid_distance(location_1, location_2)
                if distance_data:
                    distance_in_km = distance_data[1]
                    # Notify user1, and user2
                    self.notify_users(user_key_1, user_key_2, distance_in_km)
                    print("Coords under 5 km distance")
                else:
                    print("Coords above 5 km distance")

        pass

    def test_inserted_data(self, user_id):
        inserted_data = self.redis_handler.get(user_id)
        print('Inserted data ' + str(inserted_data))


if __name__ == '__main__':
    # Run some unit tests
    pass
