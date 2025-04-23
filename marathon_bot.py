import telebot
from datetime import datetime
import time
from math import radians, sin, cos, sqrt, atan2
from telebot import types
import csv
import logging
import os
import re
import psycopg2

# Налаштування логування
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if BOT_TOKEN is None:
    logger.error("Error: BOT_TOKEN environment variable not set!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

LOCATION_REQUEST_TIMEOUT = 30 # seconds
EARTH_RADIUS_KM = 6371
CSV_FILE = 'marathon_results.csv'
UKRAINIAN_RUN_URL = "https://www.ukrainian.run/#registration"
ENGLISH_RUN_URL = "https://www.ukrainian.run/en/#registration"

def calculate_distance(start_lat, start_lon, finish_lat, finish_lon):
    """Рассчитывает расстояние между двумя точками на Земле (в километрах) используя формулу Haversine."""
    start_lat, start_lon, finish_lat, finish_lon = map(radians, [start_lat, start_lon, finish_lat, finish_lon])
    dlon = finish_lon - start_lon
    dlat = finish_lat - start_lat
    a = sin(dlat / 2)**2 + cos(start_lat) * cos(finish_lat) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = EARTH_RADIUS_KM * c
    return distance

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    uk_button = types.KeyboardButton("Українська")
    en_button = types.KeyboardButton("English")
    markup.add(uk_button, en_button)
    welcome_message = "Вітаємо Вас на «Марафоні Героїв»!\nWelcome to the «Heroes Marathon»!\n\nБудь ласка, оберіть мову.\nPlease select your language."
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)
    bot.register_next_step_handler(message, process_language_selection)

def process_language_selection(message):
    chat_id = message.chat.id
    language = message.text

    if language == "Українська":
        user_data[chat_id] = {'language': 'uk'}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Пропустити")
        markup.add(skip_button)
        bot.send_message(chat_id, "Ви обрали українську мову.\nБудь ласка, введіть своє ім’я.", reply_markup=markup)
        bot.register_next_step_handler(message, process_name)
    elif language == "English":
        user_data[chat_id] = {'language': 'en'}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Skip")
        markup.add(skip_button)
        bot.send_message(chat_id, "You have selected English.\nPlease enter your name.", reply_markup=markup)
        bot.register_next_step_handler(message, process_name)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        uk_button = types.KeyboardButton("Українська")
        en_button = types.KeyboardButton("English")
        markup.add(uk_button, en_button)
        bot.send_message(chat_id, "Будь ласка, оберіть мову з наданих варіантів.\nPlease select a language from the options provided.", reply_markup=markup)
        bot.register_next_step_handler(message, process_language_selection)
        

def process_name(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if message.text == "Пропустити" or message.text == "Skip":
        user_data[chat_id]['name'] = "Не вказано" if language == 'uk' else "Not provided"
        ask_surname(message)
    elif message.text.isalpha() and len(message.text) >= 2:
        user_data[chat_id]['name'] = message.text
        ask_surname(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Будь ласка, введіть коректне ім'я (тільки літери, мінімум 2 символи).")
        elif language == 'en':
            bot.send_message(chat_id, "Please enter a valid name (letters only, minimum 2 characters).")
        bot.register_next_step_handler(message, process_name)
    
def ask_surname(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Пропустити")
        markup.add(skip_button)
        bot.send_message(chat_id, "Будь ласка, введіть своє прізвище.", reply_markup=markup)
    elif language == 'en':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Skip")
        markup.add(skip_button)
        bot.send_message(chat_id, "Please enter your surname.", reply_markup=markup)
    bot.register_next_step_handler(message, process_surname)
    
def process_surname(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if message.text == "Пропустити" or message.text == "Skip":
        user_data[chat_id]['surname'] = "Не вказано" if language == 'uk' else "Not provided"
        ask_birth_day(message)
    elif message.text.isalpha() and len(message.text) >= 2:
        user_data[chat_id]['surname'] = message.text
        ask_birth_day(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Будь ласка, введіть коректне прізвище (тільки літери, мінімум 2 символи).")
        elif language == 'en':
            bot.send_message(chat_id, "Please enter a valid surname (letters only, minimum 2 characters).")
        bot.register_next_step_handler(message, process_surname)
        
def ask_birth_day(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Пропустити")
        markup.add(skip_button)
        bot.send_message(chat_id, "Будь ласка, введіть день свого народження (1-31):", reply_markup=markup)
    elif language == 'en':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Skip")
        markup.add(skip_button)
        bot.send_message(chat_id, "Please enter the day of your birth (1-31):", reply_markup=markup)
    bot.register_next_step_handler(message, process_birth_day)

def process_birth_day(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if message.text == "Пропустити" or message.text == "Skip":
        user_data[chat_id]['birth_day'] = "Не вказано" if language == 'uk' else "Not provided"
        ask_birth_month(message)
    elif message.text.isdigit() and 1 <= int(message.text) <= 31:
        user_data[chat_id]['birth_day'] = message.text.zfill(2)
        ask_birth_month(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Невірний формат дня. Будь ласка, введіть число від 1 до 31.")
        elif language == 'en':
            bot.send_message(chat_id, "Invalid day format. Please enter a number from 1 to 31.")
        bot.register_next_step_handler(message, process_birth_day)

def ask_birth_month(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Пропустити")
        markup.add(skip_button)
        bot.send_message(chat_id, "Будь ласка, введіть місяць свого народження (1-12):", reply_markup=markup)
    elif language == 'en':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Skip")
        markup.add(skip_button)
        bot.send_message(chat_id, "Please enter the month of your birth (1-12):", reply_markup=markup)
    bot.register_next_step_handler(message, process_birth_month)

def process_birth_month(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if message.text == "Пропустити" or message.text == "Skip":
        user_data[chat_id]['birth_month'] = "Не вказано" if language == 'uk' else "Not provided"
        ask_birth_year(message)
    elif message.text.isdigit() and 1 <= int(message.text) <= 12:
        user_data[chat_id]['birth_month'] = message.text.zfill(2)
        ask_birth_year(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Невірний формат місяця. Будь ласка, введіть число від 1 до 12.")
        elif language == 'en':
            bot.send_message(chat_id, "Invalid month format. Please enter a number from 1 to 12.")
        bot.register_next_step_handler(message, process_birth_month)

def ask_birth_year(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    current_year = datetime.now().year
    if language == 'uk':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Пропустити")
        markup.add(skip_button)
        bot.send_message(chat_id, f"Будь ласка, введіть рік свого народження (1900-{current_year}):", reply_markup=markup)
    elif language == 'en':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip_button = types.KeyboardButton("Skip")
        markup.add(skip_button)
        bot.send_message(chat_id, f"Please enter the year of your birth (1900-{current_year}):", reply_markup=markup)
    bot.register_next_step_handler(message, process_birth_year)

def process_birth_year(message):
    chat_id = message.chat.id
    language = user_data.get(chat_id, {}).get('language')
    year = message.text
    current_year = datetime.now().year
    if message.text == "Пропустити" or message.text == "Skip":
        user_data[chat_id]['birth_year'] = "Не вказано" if language == 'uk' else "Not provided"
    elif year.isdigit() and 1900 <= int(year) <= current_year:
        user_data[chat_id]['birth_year'] = year
    else:
        if language == 'uk':
            bot.send_message(chat_id, f"Невірний формат року. Будь ласка, введіть рік від 1900 до {current_year}.")
        elif language == 'en':
            bot.send_message(chat_id, f"Invalid year format. Please enter a year from 1900 to {current_year}.")
        bot.register_next_step_handler(message, process_birth_year)

    # Формируем дату рождения, даже если что-то пропущено
    day = user_data[chat_id].get('birth_day', 'Не вказано' if language == 'uk' else 'Not provided')
    month = user_data[chat_id].get('birth_month', 'Не вказано' if language == 'uk' else 'Not provided')
    year = user_data[chat_id].get('birth_year', 'Не вказано' if language == 'uk' else 'Not provided')
    user_data[chat_id]['birthdate'] = f"{day}/{month}/{year}"
    user_data[chat_id]['registration_step'] = 'birth_year_received'
    ask_phone(message)
    
def ask_phone(message):
    chat_id = message.chat.id
    language = user_data.get(chat_id, {}).get('language')

    if not language:
        bot.send_message(chat_id, "Будь ласка, пройдіть попередні кроки реєстрації." if language == 'uk' else "Please complete the previous registration steps.")
        return

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    if language == 'uk':
        share_button = types.KeyboardButton(text="Поділитись", request_contact=True)
        skip_button = types.KeyboardButton(text="Пропустити")
        keyboard.add(share_button, skip_button)
        bot.send_message(chat_id, "Будь ласка, поділіться своїм номером телефону.", reply_markup=keyboard)
    elif language == 'en':
        share_button = types.KeyboardButton(text="Share", request_contact=True)
        skip_button = types.KeyboardButton(text="Skip")
        keyboard.add(share_button, skip_button)
        bot.send_message(chat_id, "Please share your phone number.", reply_markup=keyboard)
    bot.register_next_step_handler(message, process_phone)

def process_phone(message):
    chat_id = message.chat.id
    language = user_data.get(chat_id, {}).get('language', 'uk')

    if message.contact:
        phone_number = message.contact.phone_number
        user_data[chat_id]['phone_number'] = phone_number
        user_data[chat_id]['registration_step'] = 'phone_received'
        ask_location_instruction(message)
    elif message.text == "Пропустити" or message.text == "Skip":
        user_data[chat_id]['phone_number'] = "Не вказано" if language == 'uk' else "Not provided"
        user_data[chat_id]['registration_step'] = 'phone_skipped'  # Optional: Add a separate step for skipping
        ask_location_instruction(message)
    else:
        bot.send_message(chat_id, "Будь ласка, поділіться своїм номером телефону, натиснувши кнопку." if language == 'uk' else "Please share your phone number by pressing the button.")
        bot.register_next_step_handler(message, process_phone)

def ask_location_instruction(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        location_instruction = "Для участі в марафоні необхідно надати доступ до вашого місцезнаходження.\nБудь ласка, увімкніть геолокацію на своєму пристрої перед тим, як натиснути кнопку «Старт»."
    elif language == 'en':
        location_instruction = "To participate in the marathon, you need to grant access to your location.\nPlease enable location services on your device before pressing the «Start» button."
    bot.send_message(chat_id, location_instruction)
    ask_start_button(message)


def ask_start_button(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True) # Добавили one_time_keyboard=True
    if language == 'uk':
        start_button = types.KeyboardButton(text="СТАРТ", request_location=True)
        start_ready_message = "Коли Ви будете готові розпочати забіг і увімкнете геолокацію, натисніть кнопку Старт."
    elif language == 'en':
        start_button = types.KeyboardButton(text="START", request_location=True)
        start_ready_message = "When you are ready to start the run and have enabled location services, press the Start button."
    keyboard.add(start_button)
    sent_message = bot.send_message(chat_id, start_ready_message, reply_markup=keyboard)
    bot.register_next_step_handler(sent_message, handle_start_location_timeout, chat_id)

def handle_start_location_timeout(message, chat_id):
    language = user_data[chat_id]['language']
    if message.content_type != 'location':
        if 'start_location' not in user_data[chat_id]:
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            if language == 'uk':
                retry_button = types.KeyboardButton(text="Повторити СПРОБУ СТАРТ", request_location=True)
                retry_message = "Будь ласка, надайте доступ до вашого місцезнаходження, щоб розпочати забіг.\nПеревірте налаштування Telegram та увімкніть геолокацію."
            elif language == 'en':
                retry_button = types.KeyboardButton(text="Retry START", request_location=True)
                retry_message = "Please grant access to your location to start the run.\nCheck your Telegram settings and enable location services."
            keyboard.add(retry_button)
            bot.send_message(chat_id, retry_message, reply_markup=keyboard)
            bot.register_next_step_handler(message, handle_start_location)
    else:
        handle_start_location(message)


@bot.message_handler(content_types=['location'])
def handle_start_location(message):
    chat_id = message.chat.id
    if message.location is not None:
        start_latitude = message.location.latitude
        start_longitude = message.location.longitude
        start_time = datetime.now()
        user_data[chat_id]['start_location'] = (start_latitude, start_longitude)
        user_data[chat_id]['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        ask_finish_readiness(message)

def ask_finish_readiness(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if language == 'uk':
        finish_button = types.KeyboardButton(text="ФІНІШ", request_location=True)
        finish_ready_message = "Коли завершите забіг, натисніть кнопку «ФІНІШ»."
    elif language == 'en':
        finish_button = types.KeyboardButton(text="FINISH", request_location=True)
        finish_ready_message = "When you finish the run, press the «FINISH» button."
    keyboard.add(finish_button)
    sent_message = bot.send_message(chat_id, finish_ready_message, reply_markup=keyboard)
    bot.register_next_step_handler(sent_message, handle_finish_location)

@bot.callback_query_handler(func=lambda call: call.data == 'already_registered')
def handle_already_registered(call):
    chat_id = call.message.chat.id
    language = user_data[chat_id]['language']
    bot.send_message(chat_id, "🇺🇦🇺🇦 Героям Слава! 🇺🇦🇺🇦" if language == 'uk' else "🇺🇦🇺🇦 Glory to the heroes! 🇺🇦🇺🇦", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(content_types=['location'])
def handle_finish_location(message):
    chat_id = message.chat.id
    print(f"Получена геолокация для {chat_id}")
    
    if message.location is not None:
        print(f"Геолокация получена: {message.location.latitude}, {message.location.longitude}")
        finish_latitude = message.location.latitude
        finish_longitude = message.location.longitude
        finish_time = datetime.now()
        user_data[chat_id]['finish_location'] = (finish_latitude, finish_longitude)
        user_data[chat_id]['finish_time'] = finish_time.strftime("%Y-%m-%d %H:%M:%S")
        
        start_location = user_data[chat_id].get('start_location')
        print(f"Данные о старте: {start_location}")
        
        if start_location:
            start_lat, start_lon = start_location
            distance = calculate_distance(start_lat, start_lon, finish_latitude, finish_longitude)
            print(f"Расчет дистанции завершен: {distance} км")
            user_data[chat_id]['distance'] = distance
            distance_km = round(distance, 2)
            language = user_data[chat_id]['language']
            finish_message = f"🇺🇦 Ваш забіг завершено! Дякуємо за участь у «Марафоні Героїв»! 🇺🇦" if language == 'uk' else f"🇺🇦 Your run is finished! Thank you for participating in the «Heroes Marathon»! 🇺🇦"
            bot.send_message(chat_id, finish_message, reply_markup=types.ReplyKeyboardRemove())
            
            website_message = "Щоб отримати сертифікат про участь у марафоні та нагороди, потрібно зареєструватись на нашому сайті. Для цього натисніть кнопку нижче (для кращої роботи рекомендуємо відкрити у зовнішньому браузері)." if language == 'uk' else "To receive a certificate of participation in the marathon and a reward, you need to register on our website. To do this, press the button below (for better performance, we recommend opening in an external browser)."
            markup_inline = types.InlineKeyboardMarkup()
            website_button = types.InlineKeyboardButton(text="Перейти на сайт" if language == 'uk' else "Go to website", url=UKRAINIAN_RUN_URL if language == 'uk' else ENGLISH_RUN_URL)
            already_registered_button = types.InlineKeyboardButton(text="Вже зареєструвався" if language == 'uk' else "Already registered", callback_data='already_registered')
            markup_inline.add(website_button, already_registered_button)
            bot.send_message(chat_id, website_message, reply_markup=markup_inline)
            
            # Запис даних у базу даних PostgreSQL
        DATABASE_URL = os.environ.get('DATABASE_URL')
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            insert_query = """
                INSERT INTO marathon_results (
                    chat_id, name, surname, birthdate, phone_number,
                    start_time, start_latitude, start_longitude,
                    finish_time, finish_latitude, finish_longitude, distance_km
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET
                    name = %s, surname = %s, birthdate = %s, phone_number = %s,
                    start_time = %s, start_latitude = %s, start_longitude = %s,
                    finish_time = %s, finish_latitude = %s, finish_longitude = %s, distance_km = %s;
            """
            data_to_insert = (
                chat_id,
                user_data[chat_id].get('name', ''),
                user_data[chat_id].get('surname', ''),
                user_data[chat_id].get('birthdate', ''),
                user_data[chat_id].get('phone_number', ''),
                user_data[chat_id].get('start_time', ''),
                user_data[chat_id].get('start_location', ('', ''))[0],
                user_data[chat_id].get('start_location', ('', ''))[1],
                user_data[chat_id].get('finish_time', ''),
                user_data[chat_id].get('finish_location', ('', ''))[0],
                user_data[chat_id].get('finish_location', ('', ''))[1],
                user_data[chat_id].get('distance', ''),
                user_data[chat_id].get('name', ''), # Для ON CONFLICT
                user_data[chat_id].get('surname', ''), # Для ON CONFLICT
                user_data[chat_id].get('birthdate', ''), # Для ON CONFLICT
                user_data[chat_id].get('phone_number', ''), # Для ON CONFLICT
                user_data[chat_id].get('start_time', ''), # Для ON CONFLICT
                user_data[chat_id].get('start_location', ('', ''))[0], # Для ON CONFLICT
                user_data[chat_id].get('start_location', ('', ''))[1], # Для ON CONFLICT
                user_data[chat_id].get('finish_time', ''), # Для ON CONFLICT
                user_data[chat_id].get('finish_location', ('', ''))[0], # Для ON CONFLICT
                user_data[chat_id].get('finish_location', ('', ''))[1], # Для ON CONFLICT
                user_data[chat_id].get('distance', '') # Для ON CONFLICT
            )
            cur.execute(insert_query, data_to_insert)
            conn.commit()
            cur.close()
            conn.close()
            print(f"Дані користувача {chat_id} записано в базу даних PostgreSQL")
        except psycopg2.Error as e:
            logger.error(f"Помилка запису в базу даних PostgreSQL: {e}")
            bot.send_message(chat_id, "Виникла помилка при збереженні результатів забігу." if language == 'uk' else "An error occurred while saving the run results.")
    else:
        print(f"Геолокация не получена для {chat_id}")
        bot.send_message(chat_id, "Будь ласка, надайте доступ до вашого місцезнаходження." if language == 'uk' else "Please grant access to your location.")



     
if __name__ == '__main__':
    bot.infinity_polling()
