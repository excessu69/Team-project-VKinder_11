import json
import requests
from tqdm import tqdm
from work_with_data_base.interactions_with_DB import *


class VK_Bot:
    def __init__(self, gender, age, city, access_token, vk_user_id):
        self.access_token = access_token
        self.vk_user_id = vk_user_id
        self.age = age
        self.gender = '2' if gender == 'Мужской' else '1'
        self.city = city

    def integration(self):
        params = {
            'count': '1000',
            'sex': self.gender,
            'hometown': self.city,
            'age_from': self.age,
            'age_to': self.age,
            'has_photo': '1',
            'access_token': self.access_token,
            'v': '11.9.9'
        }
        try:
            response = requests.get('https://api.vk.com/method/users.search', params=params)
            response.raise_for_status()
            result = response.json()

            if result.get('response', {}).get('count', 0) != 0:
                res = result['response']['items']
                for item in tqdm(res, desc='Идет поиск...'):
                    profile_url = f"https://vk.com/id{item['id']}"
                    photos = self.get_photos(item['id'])
                    if photos:
                        first_name = item['first_name']
                        last_name = item['last_name']
                        city = self.city
                return 'Готово!'
            else:
                raise Exception('No results found')
        except requests.RequestException as e:
            print(f"Ошибка при отправке запроса: {e}")
        except Exception as e:
            print(f"Ошибка во время выполнения: {e}")
            return '&#10060; Ошибка:\nОдин или несколько параметров указаны неверно.\nПопробуйте ещё раз.'

    def get_photos(self, user_id):
        photos_params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'rev': '1',
            'access_token': self.access_token,
            'extended': '1',
            'v': '11.9.9'
        }
        try:
            photos_response = requests.get('https://api.vk.com/method/photos.get', params=photos_params)
            photos_response.raise_for_status()
            photos_result = photos_response.json()

            if 'response' in photos_result:
                photos = photos_result['response'].get('items', [])
                sorted_photos = sorted(photos, key=lambda x: x.get('likes', {}).get('count', 0), reverse=True)
                photo_urls = [photo['sizes'][-1]['url'] for photo in sorted_photos[:3]]
                return photo_urls
            else:
                return []
        except requests.RequestException as e:
            print(f"Ошибка при получении фотографий: {e}")
            return []