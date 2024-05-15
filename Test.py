import unittest
from unittest.mock import patch
from interaction_with_the_VK_bot import *


class TestVKBot(unittest.TestCase):

    def test_get_user_profile(self):
        user_info = get_user_profile(123456)
        self.assertIsNotNone(user_info)

        
        user_info = get_user_profile(999999)
        self.assertIsNone(user_info)

    def test_get_top_photos(self):
        
        photo_links = get_top_photos(123456)
        self.assertIsNotNone(photo_links)

       
        photo_links = get_top_photos(999999)
        self.assertEqual(photo_links, [])

    def test_get_city_id(self):
        
        city_id = get_city_id('Moscow')
        self.assertIsNotNone(city_id)

        
        city_id = get_city_id('InvalidCity')
        self.assertIsNone(city_id)

    def test_create_next_button(self):
        
        next_button = create_next_button()
        self.assertIsNotNone(next_button)

    def test_create_gender_keyboard(self):
        gender_keyboard = create_gender_keyboard()
        self.assertIsNotNone(gender_keyboard)

    @patch('your_code_file.write_msg')
    def test_search_users(self, mock_write_msg):
        search_users(123456, 1, 'user_token')
        mock_write_msg.assert_called()

        search_users(123456, None, 'user_token')
        mock_write_msg.assert_called()


if __name__ == '__main__':
    unittest.main()