import telebot
from datetime import datetime, timezone
import pytz
from src.database import SessionLocal
from src.models import Task
from src.config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Создание сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для управления задачами. Вот что я умею:\n" +
        "1. Создание списков задач\n" +
        "2. Добавление описания к задачам\n" +
        "3. Установка даты и времени для напоминаний\n" +
        "4. Все действия и напоминания будут в Московском времени.\n\n" +
        "Чтобы начать, используйте команду /newlist"
    )

# Обработчик команды /newlist
@bot.message_handler(commands=['newlist'])
def create_new_list(message):
    msg = bot.send_message(message.chat.id, "Введите название списка задач:")
    bot.register_next_step_handler(msg, process_list_name_step)

def process_list_name_step(message):
    list_name = message.text
    msg = bot.send_message(message.chat.id, "Введите описание задачи:")
    bot.register_next_step_handler(msg, process_description_step, list_name)

def process_description_step(message, list_name):
    description = message.text
    msg = bot.send_message(message.chat.id, "Введите дату и время в формате YYYY-MM-DD HH:MM (в Московском времени):")
    bot.register_next_step_handler(msg, process_due_date_step, list_name, description)

def process_due_date_step(message, list_name, description):
    try:
        due_date = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        # Преобразуем введенную дату и время в Московское время
        localized_due_date = MOSCOW_TZ.localize(due_date)
        save_task(message, list_name, description, localized_due_date)
        bot.send_message(message.chat.id, f"Задача '{list_name}' успешно создана!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты и времени. Попробуйте еще раз.")

# Функция для сохранения задач в базе данных
def save_task(message, list_name, description, due_date):
    db = next(get_db())
    user_time = datetime.fromtimestamp(message.date, tz=timezone.utc)

    # Преобразуем due_date в UTC
    utc_due_date = due_date.astimezone(pytz.utc)

    task = Task(
        user_id=message.chat.id,
        list_name=list_name,
        description=description,
        due_date=utc_due_date,
        created_at=user_time
    )
    db.add(task)
    db.commit()

# Функция для отправки напоминаний
def send_reminders():
    db = next(get_db())
    tasks = db.query(Task).all()
    now = datetime.now(MOSCOW_TZ).astimezone(pytz.utc)  # Текущее время в Московском времени преобразуем в UTC

    for task in tasks:
        task_due_date = task.due_date.astimezone(pytz.utc)
        if now >= task_due_date:
            bot.send_message(task.user_id, f"Напоминание о задаче: {task.list_name}\nОписание: {task.description}")
            db.delete(task)
            db.commit()

@bot.message_handler(func=lambda message: True)
def handle_unknown_commands(message):
    bot.send_message(
        message.chat.id,
        "Извините, я не понимаю эту команду. Пожалуйста, используйте /start для получения информации о доступных командах."
    )

@bot.message_handler(commands=['newlist'])
def secret(message):
    bot.send_message(message.chat.id,'секретов нет')

# Настройка периодического выполнения функции напоминаний
import threading
import time

def reminder_thread():
    while True:
        send_reminders()
        time.sleep(60)  # Проверка каждые 60 секунд

reminder = threading.Thread(target=reminder_thread)
reminder.start()

# Запуск бота
bot.polling(none_stop=True)
