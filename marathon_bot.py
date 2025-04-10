import telebot
from datetime import datetime
import time
from math import radians, sin, cos, sqrt, atan2
from telebot import types
import csv
import logging
import re
import os

# Налаштування логування
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if BOT_TOKEN is None:
    print("Error: BOT_TOKEN environment variable not set!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
LOCATION_REQUEST_TIMEOUT = 30  # seconds
EARTH_RADIUS_KM = 6371
CSV_FILE = 'marathon_results.csv'

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
        bot.send_message(chat_id, "Ви обрали українську мову. Будь ласка, введіть своє ім’я.", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_name)
    elif language == "English":
        user_data[chat_id] = {'language': 'en'}
        bot.send_message(chat_id, "You have selected English. Please enter your name.", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_name)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        uk_button = types.KeyboardButton("Українська")
        en_button = types.KeyboardButton("English")
        markup.add(uk_button, en_button)
        bot.send_message(chat_id, "Будь ласка, оберіть мову з наданих варіантів.\nPlease select a language from the options provided.", reply_markup=markup)
        bot.register_next_step_handler(message, process_language_selection)

def get_name(message):
    chat_id = message.chat.id
    name = message.text
    language = user_data[chat_id]['language']
    if name.isalpha():
        user_data[chat_id]['name'] = name
        ask_surname(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Будь ласка, введіть коректне ім'я (тільки літери).")
        elif language == 'en':
            bot.send_message(chat_id, "Please enter a valid name (letters only).")
        bot.register_next_step_handler(message, get_name)

def ask_surname(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        bot.send_message(chat_id, "Будь ласка, введіть своє прізвище.")
    elif language == 'en':
        bot.send_message(chat_id, "Please enter your surname.")
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    chat_id = message.chat.id
    surname = message.text
    language = user_data[chat_id]['language']
    if surname.isalpha():
        user_data[chat_id]['surname'] = surname
        ask_birth_day(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Будь ласка, введіть коректне прізвище (тільки літери).")
        elif language == 'en':
            bot.send_message(chat_id, "Please enter a valid surname (letters only).")
        bot.register_next_step_handler(message, get_surname)

def ask_birth_day(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        bot.send_message(chat_id, "Будь ласка, введіть день свого народження (1-31):")
    elif language == 'en':
        bot.send_message(chat_id, "Please enter the day of your birth (1-31):")
    bot.register_next_step_handler(message, get_birth_day)

def get_birth_day(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    day = message.text
    if day.isdigit() and 1 <= int(day) <= 31:
        user_data[chat_id]['birth_day'] = day.zfill(2) # Добавляем ведущий ноль, если нужно
        ask_birth_month(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Невірний формат дня. Будь ласка, введіть число від 1 до 31.")
        elif language == 'en':
            bot.send_message(chat_id, "Invalid day format. Please enter a number from 1 to 31.")
        bot.register_next_step_handler(message, get_birth_day)

def ask_birth_month(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if language == 'uk':
        bot.send_message(chat_id, "Будь ласка, введіть місяць свого народження (1-12):")
    elif language == 'en':
        bot.send_message(chat_id, "Please enter the month of your birth (1-12):")
    bot.register_next_step_handler(message, get_birth_month)

def get_birth_month(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    month = message.text
    if month.isdigit() and 1 <= int(month) <= 12:
        user_data[chat_id]['birth_month'] = month.zfill(2) # Добавляем ведущий ноль, если нужно
        ask_birth_year(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, "Невірний формат місяця. Будь ласка, введіть число від 1 до 12.")
        elif language == 'en':
            bot.send_message(chat_id, "Invalid month format. Please enter a number from 1 to 12.")
        bot.register_next_step_handler(message, get_birth_month)

def ask_birth_year(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    current_year = datetime.now().year
    if language == 'uk':
        bot.send_message(chat_id, f"Будь ласка, введіть рік свого народження (1900-{current_year}):")
    elif language == 'en':
        bot.send_message(chat_id, f"Please enter the year of your birth (1900-{current_year}):")
    bot.register_next_step_handler(message, get_birth_year)


def get_birth_year(message):
    chat_id = message.chat.id
    language = user_data.get(chat_id, {}).get('language')
    year = message.text
    current_year = datetime.now().year
    if year.isdigit() and 1900 <= int(year) <= current_year:
        user_data[chat_id]['birth_year'] = year
        user_data[chat_id]['birthdate'] = f"{user_data[chat_id]['birth_day']}/{user_data[chat_id]['birth_month']}/{user_data[chat_id]['birth_year']}"
        user_data[chat_id]['registration_step'] = 'birth_year_received'
        ask_phone(message)
    else:
        if language == 'uk':
            bot.send_message(chat_id, f"Невірний формат року. Будь ласка, введіть рік від 1900 до {current_year}.")
        elif language == 'en':
            bot.send_message(chat_id, f"Invalid year format. Please enter a year from 1900 to {current_year}.")
        bot.register_next_step_handler(message, get_birth_year)

def ask_phone(message):
    chat_id = message.chat.id
    language = user_data.get(chat_id, {}).get('language')

    if not language:
        bot.send_message(chat_id, "Будь ласка, пройдіть попередні кроки реєстрації." if language == 'uk' else "Please complete the previous registration steps.")
        return

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    if language == 'uk':
        share_button = types.KeyboardButton(text="Поділитись номером телефону", request_contact=True)
        keyboard.add(share_button)
        bot.send_message(chat_id, "Будь ласка, поділіться своїм номером телефону, натиснувши кнопку нижче.", reply_markup=keyboard)
    elif language == 'en':
        share_button = types.KeyboardButton(text="Share phone number", request_contact=True)
        keyboard.add(share_button)
        bot.send_message(chat_id, "Please share your phone number by pressing the button below.", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_phone)


    
@bot.message_handler(content_types=['contact'])
def get_phone(message):
    chat_id = message.chat.id
    if message.contact is not None:
        phone_number = message.contact.phone_number
        user_data[chat_id]['phone_number'] = phone_number
        user_data[chat_id]['registration_step'] = 'phone_received' # Обновляем шаг регистрации
        ask_location_instruction(message)
    else:
        language = user_data.get(chat_id, {}).get('language', 'uk')
        bot.send_message(chat_id, "Будь ласка, поділіться своїм номером телефону, натиснувши кнопку." if language == 'uk' else "Please share your phone number by pressing the button.")
        bot.register_next_step_handler(message, get_phone) # Оставляем обработчик на случай неправильного ввода

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
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
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
    language = user_data.get(chat_id, {}).get('language', 'uk')
    if message.content_type != 'location':
        time.sleep(LOCATION_REQUEST_TIMEOUT)
        if 'start_location' not in user_data.get(chat_id, {}):
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            if language == 'uk':
                retry_button = types.KeyboardButton(text="Повторити СПРОБУ СТАРТ", request_location=True)
                retry_message = "Будь ласка, надайте доступ до вашого місцезнаходження, щоб розпочати забіг.\nПеревірте налаштування Telegram та увімкніть геолокацію."
            elif language == 'en':
                retry_button = types.KeyboardButton(text="Retry START", request_location=True)
                retry_message = "Please grant access to your location to start the run.\nCheck your Telegram settings and enable location services."
            keyboard.add(retry_button)
            bot.send_message(chat_id, retry_message, reply_markup=keyboard)
            bot.register_next_step_handler(bot.send_message(chat_id, "Очікую на вашу геолокацію..." if language == 'uk' else "Waiting for your location..."), handle_start_location)
        else:
            ask_finish_readiness(message)
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
    bot.send_message(chat_id, finish_ready_message, reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_finish_location)

@bot.message_handler(content_types=['location'])
def handle_finish_location(message):
    chat_id = message.chat.id
    language = user_data[chat_id]['language']
    if message.location is not None:
        finish_latitude = message.location.latitude
        finish_longitude = message.location.longitude
        finish_time = datetime.now()
        user_data[chat_id]['finish_location'] = (finish_latitude, finish_longitude)
        user_data[chat_id]['finish_time'] = finish_time.strftime("%Y-%m-%d %H:%M:%S")

        start_location = user_data[chat_id].get('start_location')
        if start_location:
            start_lat, start_lon = start_location
            distance = calculate_distance(start_lat, start_lon, finish_latitude, finish_longitude)
            user_data[chat_id]['distance'] = distance

            distance_km = round(distance, 2)

            markup_inline = types.InlineKeyboardMarkup()
            website_url = "https://www.ukrainian.run/#registration" if language == 'uk' else "https://www.ukrainian.run/en/#registration"
            website_button = types.InlineKeyboardButton(text="Перейти на сайт" if language == 'uk' else "Go to website", url=website_url)
            markup_inline.add(website_button)

            finish_message = f"Ваш забіг завершено! Подолана дистанція: {distance_km} км. Дякуємо за участь у «Марафоні Героїв»! 🇺🇦" if language == 'uk' else f"Your run is finished! Distance covered: {distance_km} km. Thank you for participating in the «Heroes Marathon»! 🇺🇦"
            website_message = "Щоб отримати сертифікат про участь у марафоні та нагороди, потрібно зареєструватись на нашому сайті. Для цього натисніть кнопку нижче (для кращої роботи рекомендуємо відкрити у зовнішньому браузері)." if language == 'uk' else "To receive a certificate of participation in the marathon and a reward, you need to register on our website. To do this, press the button below (for better performance, we recommend opening in an external browser)."

            bot.send_message(chat_id, finish_message, reply_markup=types.ReplyKeyboardRemove())
            bot.send_message(chat_id, website_message, reply_markup=markup_inline)

            # Запись данных в CSV файл
            try:
                with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    if csvfile.tell() == 0:
                        writer.writerow(['Chat ID', 'Имя', 'Фамилия', 'Дата рождения', 'Номер телефона', 'Время старта', 'Широта старта', 'Долгота старта', 'Время финиша', 'Широта финиша', 'Долгота финиша', 'Дистанция (км)'])
                    writer.writerow([
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
                        user_data[chat_id].get('distance', '')
                    ])
                print(f"Данные пользователя {chat_id} записаны в {CSV_FILE}")
            except Exception as e:
                print(f"Ошибка записи в CSV файл: {e}")
                bot.send_message(chat_id, "Виникла помилка при збереженні результатів забігу." if language == 'uk' else "An error occurred while saving the run results.")

            # Очистка данных пользователя после завершения забега (по желанию)
            # del user_data[chat_id]

        else:
            error_message = "Помилка: не вдалося знайти дані про старт. Будь ласка, почніть забіг спочатку." if language == 'uk' else "Error: start data not found. Please start the run again."
            bot.send_message(chat_id, error_message)

if __name__ == '__main__':
    print("Bot started...")
    bot.polling(none_stop=True)
