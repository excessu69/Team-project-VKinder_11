import psycopg2
from psycopg2.extras import Json
from work_with_data_base.interactions_with_DB import (User_DB)
from work_with_data_base.user_data.DB_login_info import database, user, password

if __name__ == '__main__':
    with psycopg2.connect(database=database, user=user, password=password) as conn:
        with conn.cursor() as cur:

            # Создаю пользователей
            put_user1 = User_DB(conn, cur, 'female', None, 'Stokholm', 'Maria',
                             'Reinolds', 'jbjkcmck',
                             photo_links=Json({
                                 1: 'https://i.yapx.cc/OMDU5.jpg',
                                 2: 'https://i.pinimg.com/736x/7c/24/cc/7c24ccdd8698cce9aa18b13ec6b59082.jpg',
                                 3: 'https://www.youtube.com/watch?v=1HVWTrbgmxw'
                             }))
            put_user2 = User_DB(conn, cur, 'male', '18', 'Stokholm', 'Leo', 'Peterson', 'sxjdvbkbc')
            put_user3 = User_DB(conn, cur, None, '13', 'Valle del sol', 'Xio', 'Mala-Suerte', 'israpsidian')

            get_user1 = User_DB(conn, cur, city='Stokholm')
            get_user2 = User_DB(conn, cur, gender='male', age='18', city='Stokholm')
            get_user3 = User_DB(conn, cur, age='13', city='valle del sol')

            # Заполняю таблицу пользователей
            put_user1.put_a_person()
            put_user2.put_a_person()
            put_user3.put_a_person()

            # Достаю пользователей по совпадениям
            get_user1.get_a_person()
            get_user2.get_a_person()
            get_user3.get_a_person()

    # тестирую функцию to_like
    put_user2.to_like(3)
    put_user2.to_like(2)
    put_user2.to_like(15)

    # тестирую функцию to_block
    put_user1.to_block(1)
    put_user1.to_block(19)
    put_user1.to_block(2)
