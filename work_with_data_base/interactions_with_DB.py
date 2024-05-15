import logging

import psycopg2
import json


class User_DB:
    def __init__(self, conn, cur, gender=None, age=None, city=None, first_name=None, last_name=None,
                 account_link=None, photo_links=None):
        self.conn = conn
        self.cur = cur
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.age = age
        self.city = city
        self.account_link = account_link
        self.photo_links = photo_links
        self.user_id = self.id_by_link()
        self.exists = False

    def get_a_person(self) -> tuple:
        self.cur.execute('''
            SELECT *
            FROM user_account
            WHERE
                gender iLIKE %s
                OR age = %s
                OR city iLIKE %s
            ORDER BY
                gender iLIKE %s DESC, gender,
                age = %s DESC, age,
                city iLIKE %s DESC, city;   
        ''', (self.gender, self.age, self.city, self.gender, self.age, self.city))
        return self.cur.fetchone()

    def check_double(self) -> bool:
        self.cur.execute(f'''
            SELECT count(1) > 0
            FROM user_account
            WHERE account_link = '{self.account_link}'
            ''')
        result = self.cur.fetchone()
        return result[0]

    def put_a_person(self):
        try:
            if self.check_double() is not True:
                photo_links_json = json.dumps(self.photo_links)
                # Выполняем SQL-запрос для вставки данных пользователя в таблицу user_account
                self.cur.execute('''
                        INSERT INTO user_account (first_name, last_name, gender, age, city, account_link, photo_links)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (self.first_name, self.last_name, self.gender, self.age,
                          self.city, self.account_link, photo_links_json))

                # Получаем ID только что вставленной записи
                self.last_inserted_user_id = self.cur.fetchone()[0]
                self.exists = True  # Задаем флаг exists в True, чтобы показать, что пользователь успешно добавлен
                print("User successfully inserted into the database.")
        except Exception as e:
            print("Error occurred while inserting user into the database:", e)

    def id_by_link(self) -> int:
        try:
            self.cur.execute('''
                SELECT id 
                FROM user_account
                WHERE account_link = %s
            ''', (self.account_link,))
            user_id = int(self.cur.fetchone()[0])
        except TypeError:
            user_id = None
        return user_id

    def to_like(self, like_id):
        try:
            if self.user_id != like_id:
                with self.conn:
                    with self.conn.cursor() as cur:
                        cur.execute('''
                            INSERT INTO to_like(user_account_id, liked_account_id) VALUES(%s, %s)
                        ''', (self.user_id, like_id))
                        self.put_a_person()
            else:
                print('Так нельзя!')
        except psycopg2.errors.ForeignKeyViolation:
            print('Такого пользователя не существует')

    def to_block(self, block_id):
        try:
            if self.user_id != block_id:
                with self.conn:
                    with self.conn.cursor() as cur:
                        cur.execute('''
                            INSERT INTO to_block(user_account_id, blocked_account_id) VALUES(%s, %s)
                        ''', (self.user_id, block_id))
                        self.put_a_person()
            else:
                print('Нельзя заблокировать самого себя')
        except psycopg2.errors.ForeignKeyViolation:
            print('Такого пользователя не существует')

    def check_if_exists(self):
        """
        Проверяет, существует ли пользователь с такими же данными в базе данных.
        """
        try:
            self.cur.execute(
                "SELECT id FROM user_account WHERE first_name = %s AND last_name = %s AND gender = %s AND age = %s AND city = %s",
                (self.first_name, self.last_name, self.gender, self.age, self.city))
            result = self.cur.fetchone()
            self.exists = result is not None
        except Exception as e:
            logging.error(f"Error checking if user exists: {e}")
            self.exists = False

    def get_existing_user_id(self):
        """
        Получает ID существующего пользователя из базы данных.
        """
        try:
            self.cur.execute(
                "SELECT id FROM user_account WHERE first_name = %s AND last_name = %s AND gender = %s AND age = %s AND city = %s",
                (self.first_name, self.last_name, self.gender, self.age, self.city))
            user_id = self.cur.fetchone()[0]
            return user_id
        except Exception as e:
            logging.error(f"Error getting existing user ID: {e}")
            return None


class LikeBlockDB:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def add_to_like(self, user_id, liked_user_id):
        """
        Добавляет информацию о понравившемся пользователе в базу данных.
        Args:
            user_id (int): ID пользователя, который поставил "Like".
            liked_user_id (int): ID пользователя, которому поставили "Like".
        """
        try:
            self.cur.execute("INSERT INTO to_like (user_account_id, liked_account_id) VALUES (%s, %s)",
                             (user_id, liked_user_id))
            self.conn.commit()
            logging.info(f"Added Like: User ID {user_id} liked User ID {liked_user_id}")
        except Exception as e:
            logging.error(f"Error adding Like: {e}")
            self.conn.rollback()

    def add_to_block(self, user_id, blocked_user_id):
        """
        Добавляет информацию о заблокированном пользователе в базу данных.
        Args:
            user_id (int): ID пользователя, который поставил "ЧС".
            blocked_user_id (int): ID пользователя, которому поставили "ЧС".
        """
        try:
            self.cur.execute("INSERT INTO to_block (user_account_id, blocked_account_id) VALUES (%s, %s)",
                             (user_id, blocked_user_id))
            self.conn.commit()
            logging.info(f"Added Block: User ID {user_id} blocked User ID {blocked_user_id}")
        except Exception as e:
            logging.error(f"Error adding Block: {e}")
            self.conn.rollback()
