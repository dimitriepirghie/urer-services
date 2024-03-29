import requests
import unittest
import json


class TestSocialMS(unittest.TestCase):
    def setUp(self):
        self.api_key = '234fa0234nasfkj238dsf'
        self.transportation_api_url = 'http://0.0.0.0'
        self.transportation_api_port = '5002'
        self.transportation_api_end_point = 'new_event'

    def test_new_event_method_not_allowed(self):
        """
        new_event end_point should accept only POST
        :return:
        """
        uri_end_point = "{}:{}/{}".format(self.transportation_api_url, self.transportation_api_port,
                                          self.transportation_api_end_point)

        reply = requests.get(uri_end_point)
        self.assertEqual(reply.status_code, 405)

        reply = requests.put(uri_end_point)
        self.assertEqual(reply.status_code, 405)

        reply = requests.head(uri_end_point)
        self.assertEqual(reply.status_code, 405)

        # Test Post Method
        reply = requests.post(uri_end_point)
        self.assertNotEqual(reply.status_code, 405)

        reply = requests.patch(uri_end_point)
        self.assertEqual(reply.status_code, 405)

    def test_new_event_bad_post_request(self):
        """
        new event post data should be a valid json
        :return:
        """
        uri_end_point = "{}:{}/{}".format(self.transportation_api_url, self.transportation_api_port,
                                          self.transportation_api_end_point)

        post_data = 'Not a valid json string'
        reply = requests.post(uri_end_point, data=post_data)
        self.assertEqual(reply.status_code, 400)

    def test_new_event_post_valid_json(self):
        """
        new event post data should be a valid json
        :return:
        """
        uri_end_point = "{}:{}/{}".format(self.transportation_api_url, self.transportation_api_port,
                                          self.transportation_api_end_point)

        post_data = json.dumps({'key': self.api_key,
                                'response_at': '',
                                'request_id': ''
                                })
        reply = requests.post(uri_end_point, data=post_data)
        self.assertEqual(reply.status_code, 201)

    def test_new_event_not_valid_api_key(self):
        """
        new event post data should be a valid json
        :return:
        """
        uri_end_point = "{}:{}/{}".format(self.transportation_api_url, self.transportation_api_port,
                                          self.transportation_api_end_point)

        post_data = json.dumps({'key': 'invalid_api_key',
                                'response_at': '',
                                'request_id': ''
                                })
        reply = requests.post(uri_end_point, data=post_data)
        self.assertEqual(reply.status_code, 401)


if __name__ == '__main__':
    unittest.main()
