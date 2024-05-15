import logging
import random
import psycopg2
import vk_api
from datetime import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from Token import community_token, user_token
from work_with_data_base.interactions_with_DB import User_DB, LikeBlockDB
from work_with_data_base.user_data.DB_login_info import database, user, password

conn = psycopg2.connect(database=database, user=user, password=password)
cur = conn.cursor()

# Логирование
logging.basicConfig(filename='app.log', level=logging.INFO)

try:
    vk = vk_api.VkApi(token=community_token)
    longpoll = VkLongPoll(vk)
    vk_user_token = vk_api.VkApi(token=user_token)
except Exception as e:
    logging.error(f"Error initializing VK API: {e}")
    raise

answer_list = ['Привет!', 'Приветствую!', 'Здравствуйте!']
hello_list = ['Привет', 'привет', 'Хай', 'хай', 'Начать', 'Start', 'Начать поиск']
favorite_users = []
shown_users = []


def write_msg(user_id, message, photos=None, photo_links=None, keyboard=None):
    """
    Отправляет сообщение пользователю с опциональными вложениями (фотографиями),
    ссылками на фотографии и пользовательской клавиатурой.

    Args: user_id (int): ID пользователя, которому отправляется сообщение.
          message (str): Текст сообщения.
          photos (list, optional): Список вложенных фотографий.
          photo_links (list, optional): Список ссылок на фотографии.
          keyboard (VkKeyboard, optional): Пользовательская клавиатура.
    """
    try:
        params = {'user_id': user_id, 'random_id': random.randrange(10 ** 7)}
        if message:
            params['message'] = message
        if keyboard is not None:
            params['keyboard'] = keyboard
        attachments = []
        if photos:
            attachments.extend(photos)
        if photo_links:
            attachments.extend(photo_links)
        if attachments:
            params['attachment'] = ','.join(attachments)
        vk.method('messages.send', params)
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        raise


def get_user_profile(user_id):
    """
    Получает информацию о профиле пользователя по его ID.
    Args: user_id (int): ID пользователя.
    Returns:
        dict: Информация о профиле пользователя.
    """
    try:
        user_info = vk.method('users.get', {'user_ids': user_id, 'fields': 'sex,bdate,city'})
        return user_info[0]
    except Exception as e:
        logging.error(f"Error getting user profile: {e}")
        raise


def get_top_photos(user_id):
    """
    Получает фотографии вариантов.
    Args: user_id (int): ID пользователя.
    Returns:
        list: Список ссылок на топ-3 фотографии.
    """
    try:
        photos = vk_user_token.method('photos.getAll', {'owner_id': user_id, 'extended': 1})
        sorted_photos = sorted(photos['items'], key=lambda x: x['likes']['count'], reverse=True)
        top_photos = sorted_photos[:3]
        photo_links = [photo['sizes'][-1]['url'] for photo in top_photos]
        return photo_links
    except vk_api.exceptions.ApiError as e:
        if e.code == 30:
            return []
        else:
            logging.error(f"Error getting top photos: {e}")
            raise


def get_user_age(birthdate_str):
    if birthdate_str:
        # Если год не указан, предполагаем текущий год
        if len(birthdate_str.split('.')) == 2:
            birthdate_str_full = birthdate_str + '.' + str(datetime.now().year)
        else:
            birthdate_str_full = birthdate_str
        birthdate = datetime.strptime(birthdate_str_full, '%d.%m.%Y')
        current_date = datetime.now()
        age = current_date.year - birthdate.year - (
                    (current_date.month, current_date.day) < (birthdate.month, birthdate.day))
        return age
    else:
        return -1


def get_city_id(city_name):
    """
    Получает ID города по его названию.
    Args: city_name (str): Название города.
    Returns:
        int: ID города.
    """
    city = vk_user_token.method('database.getCities', {'q': city_name})
    return city['items'][0]['id'] if city['count'] > 0 else None


def create_next_button():
    """
    Создает клавиатуру с кнопкой "Далее".
    Returns:
        VkKeyboard: Объект клавиатуры с кнопкой "Далее".
    """
    try:
        next_button = VkKeyboard(one_time=False, inline=True)
        next_button.add_button('Далее', color=VkKeyboardColor.PRIMARY)
        return next_button
    except Exception as e:
        logging.error(f"Error in create_next_button: {e}")
        return None


def create_gender_keyboard():
    """
    Создает клавиатуру с кнопками "Мужчина" и "Женщина".
    Returns:
        VkKeyboard: Объект клавиатуры с кнопками "Мужчина" и "Женщина".
    """
    try:
        gender_keyboard = VkKeyboard(one_time=False, inline=True)
        gender_keyboard.add_button('Мужчина', color=VkKeyboardColor.PRIMARY)
        gender_keyboard.add_button('Женщина', color=VkKeyboardColor.PRIMARY)
        return gender_keyboard
    except Exception as e:
        logging.error(f"Error in create_gender_keyboard: {e}")
        return None


def create_like_button():
    """
    Создает клавиатуру с кнопкой "Like".
    Returns:
        VkKeyboard: Объект клавиатуры с кнопкой "Like".
    """
    try:
        like_button = VkKeyboard(one_time=False, inline=True)
        like_button.add_button('Like', color=VkKeyboardColor.POSITIVE)
        return like_button
    except Exception as e:
        logging.error(f"Error in create_like_button: {e}")
        return None


def create_block_button():
    """
    Создает клавиатуру с кнопкой "ЧС" (Черный список).
    Returns:
        VkKeyboard: Объект клавиатуры с кнопкой "ЧС".
    """
    try:
        block_button = VkKeyboard(one_time=False, inline=True)
        block_button.add_button('ЧС', color=VkKeyboardColor.NEGATIVE)
        return block_button
    except Exception as e:
        logging.error(f"Error in create_block_button: {e}")
        return None


def search_users(user_id, criteria, user_token):
    """
    Выполняет поиск пользователей по заданным критериям.
    Args: user_id (int): ID пользователя, выполняющего поиск.
          criteria (int): Критерий поиска (пол).
          user_token (str): Токен пользователя для доступа к API VK.
    """

    user_profile = get_user_profile(user_id)
    user_city_name = user_profile.get('city', {}).get('title', '')
    user_city_id = get_city_id(user_city_name)

    if user_city_id is None:
        write_msg(user_id, 'Не удалось определить ваш город.')
        return
    user_age = 2024 - int(user_profile['bdate'].split('.')[-1])

    users = vk_api.VkApi(token=user_token).method('users.search',
                                                  {'count': 10, 'fields': 'photo_200', 'sex': criteria,
                                                   'city': user_city_id, 'age_from': user_age - 2,
                                                   'age_to': user_age + 2})
    if users['items']:
        available_users = [user for user in users['items'] if user['id'] not in shown_users]
        if available_users:
            random_user = random.choice(available_users)
            user_info = f"{random_user['first_name']} {random_user['last_name']}\nhttps://vk.com/id{random_user['id']}"
            user_profile_link = f"https://vk.com/id{random_user['id']}"
            write_msg(user_id, f"{user_info}\n")

            photo_links = get_top_photos(random_user['id'])
            for link in photo_links:
                write_msg(user_id, 'Фотография:', photo_links=[link])

            shown_users.append(random_user['id'])

            keyboard = VkKeyboard(one_time=False, inline=True)
            keyboard.add_button('Далее', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Like', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('ЧС', color=VkKeyboardColor.NEGATIVE)
            write_msg(user_id, "Выберите действие:", keyboard=keyboard.get_keyboard())



        else:
            write_msg(user_id, 'Не удалось найти подходящих пользователей.')

    else:
        write_msg(user_id, 'Не удалось найти подходящих пользователей.')


try:
    criteria = None

except Exception as e:
    logging.error(f"Error in other functions: {e}")

last_inserted_user_id = None


# Основной цикл
def main_loop():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                user_id = event.user_id  # Получаем ID пользователя
                if request == 'Начать' or request in hello_list:
                    # Получаем информацию о профиле пользователя
                    user_profile = get_user_profile(user_id)
                    first_name = user_profile.get('first_name', '')
                    last_name = user_profile.get('last_name', '')
                    gender_mapping = {1: 'Женщина', 2: 'Мужчина', 0: 'Пол не указан', 3: 'Пол не указан'}
                    gender = gender_mapping.get(user_profile.get('sex'))
                    city = user_profile.get('city', {}).get('title', None)
                    birthdate_str = user_profile.get('bdate', None)
                    age = get_user_age(birthdate_str)

                    # Вставляем данные пользователя в таблицу user_account
                    user_db = User_DB(conn, cur,
                                      gender=gender,
                                      age=age,
                                      city=city,
                                      first_name=first_name,
                                      last_name=last_name,
                                      account_link=f"https://vk.com/id{user_id}")
                    user_db.check_if_exists()

                    like_block_db = LikeBlockDB(conn)

                    # Если пользователь уже существует, получаем его ID из базы данных
                    if user_db.exists:
                        user_id_in_db = user_db.get_existing_user_id()
                        write_msg(user_id, f"Пользователь уже существует в базе данных с ID {user_id_in_db}")
                        like_block_db.add_to_like(user_id_in_db, None)
                        conn.commit()
                    else:

                        user_db.put_a_person()
                        conn.commit()
                        user_id_in_db = cur.lastrowid
                        write_msg(user_id, f"Пользователь {user_id_in_db} успешно добавлен в базу данных!")
                        # like_block_db.add_to_like(user_id_in_db, None)
                        conn.commit()


                    write_msg(user_id, f'{random.choice(answer_list)}')
                    write_msg(user_id,
                              f'Подскажи, кого мы ищем?\nУкажи пол:',
                              keyboard=create_gender_keyboard().get_keyboard())
                elif request.lower() == 'мужчина' or request.lower() == 'женщина':
                    criteria = 2 if request.lower() == 'мужчина' else 1
                    search_users(user_id, criteria, user_token)
                elif request == 'Далее':
                    if criteria:
                        search_users(user_id, criteria, user_token)
                    else:
                        write_msg(user_id, 'Сначала укажите пол.')
                elif request == 'Like' or request == 'ЧС':
                    if not shown_users:
                        write_msg(user_id, 'Сначала найдите подходящего пользователя.')
                        continue

                    last_shown_user_id = shown_users[-1]
                    last_shown_user_info = get_user_profile(last_shown_user_id)
                    last_shown_user_photos = get_top_photos(last_shown_user_id)

                    birthdate_str = last_shown_user_info.get('bdate', None)
                    age = get_user_age(birthdate_str)
                    gender_mapping = {1: 'Женщина', 2: 'Мужчина', 0: 'Пол не указан', 3: 'Пол не указан'}
                    gender = gender_mapping.get(last_shown_user_info.get('sex'))
                    city = last_shown_user_info['city']['title'] if 'city' in last_shown_user_info else None

                    user_db = User_DB(conn, cur,
                                      gender=gender,
                                      age=age,
                                      city=city,
                                      first_name=last_shown_user_info['first_name'],
                                      last_name=last_shown_user_info['last_name'],
                                      account_link=f"https://vk.com/id{last_shown_user_id}",
                                      photo_links=last_shown_user_photos)


                    like_block_db = LikeBlockDB(conn)


                    if request == 'Like':
                        user_db.put_a_person()
                        write_msg(user_id, 'Вы добавили вариант в список понравившихся.')
                        conn.commit()
                        if user_db.exists:
                            user_id_in_db_like = user_db.get_existing_user_id()
                            write_msg(user_id, f"Пользователь уже существует в базе данных с ID {user_id_in_db_like}")
                            like_block_db.add_to_like(user_id_in_db, user_id_in_db_like)
                            conn.commit()



                        else:
                            user_id_in_db_like = cur.lastrowid
                            like_block_db.add_to_like(user_id_in_db, user_id_in_db_like)
                            write_msg(user_id,f"Пользователь {user_id_in_db_like} успешно добавлен в базу данных!")
                            conn.commit()



                    elif request == 'ЧС':
                        user_db.put_a_person()  # Пользователь не понравился
                        write_msg(user_id, 'Вы добавили вариант в черный список.')
                        conn.commit()

                        if user_db.exists:
                            user_id_in_db_block = user_db.get_existing_user_id()
                            write_msg(user_id, f"Пользователь уже существует в базе данных с ID {user_id_in_db_block}")
                            like_block_db.add_to_block(user_id_in_db, user_id_in_db_block)
                            conn.commit()

                        else:
                            user_id_in_db_block = cur.lastrowid
                            write_msg(user_id, f"Пользователь {user_id_in_db_block} успешно добавлен в базу данных!")
                            like_block_db.add_to_block(user_id_in_db, user_id_in_db_block)
                            conn.commit()







                    if criteria:
                        if last_shown_user_id in shown_users:
                            shown_users.remove(last_shown_user_id)
                        search_users(user_id, criteria, user_token)
                    else:
                        write_msg(user_id, 'Сначала укажите пол.')




try:
    main_loop()
except Exception as e:
    logging.error(f"Error in main loop: {e}")
    raise
