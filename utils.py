import logging
import asyncio
import requests
import sqlite3
from aiogram import Bot
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import AUTH_TOKEN, API_TOKEN
import re

conn = sqlite3.connect('threads.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS threads (id INTEGER PRIMARY KEY, thread_id TEXT UNIQUE)''')
conn.commit()

def bump_thread(thread_id):
    url = f"https://api.zelenka.guru/threads/{thread_id}/bump"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {AUTH_TOKEN}"
    }
    response = requests.post(url, headers=headers)
    response_data = response.json()
    logging.info(f"Response for thread {thread_id}: {response_data}")
    if response.status_code == 200:
        try:
            error_message = response_data["errors"][0]
            time_match = re.search(r'(\d+)\s+часов\s+(\d+)\s+минут\s+(\d+)\s+секунд', error_message)
            if time_match:
                hours, minutes, seconds = map(int, time_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds
                return (
                    total_seconds,
                    f"<code>{thread_id}</code>\nСогласно вашим правам вы можете поднимать тему раз в 12 часов. Вы должны подождать {total_seconds} секунд, чтобы поднять тему {thread_id}."
                )
            else:
                return (
                    None,
                    error_message.replace('<br>', '\n')
                )
        except (IndexError, KeyError):
            return (
                None,
                f"Вы подняли тему {thread_id}."
            )
    else:
        return (
            None,
            f"Ошибка при поднятии темы {thread_id}: {response.status_code}"
        )

def get_all_threads():
    cursor.execute("SELECT thread_id FROM threads")
    return cursor.fetchall()

def add_thread_to_db(thread_id):
    try:
        cursor.execute("INSERT INTO threads (thread_id) VALUES (?)", (thread_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_thread_from_db(thread_id):
    cursor.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
    conn.commit()

def get_thread_title(thread_id):
    url = f"https://api.zelenka.guru/threads/{thread_id}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {AUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        thread_data = response.json()
        return thread_data["thread"]["thread_title"]
    return "Unknown Title"

async def send_message_with_main_menu(message: Message, text: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Главное меню", callback_data='main_menu')
    await message.answer(text, reply_markup=builder.as_markup())

async def send_message_with_start_button(message: Message, text: str, parse_mode: str = None):
    builder = InlineKeyboardBuilder()
    builder.button(text="Начать заново", callback_data='start')
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode=parse_mode)

async def scheduled_bump(bot):
    while True:
        await asyncio.sleep(12 * 3600)
        await bump_all_threads(bot)

async def bump_all_threads(bot, user_id=None):
    threads = get_all_threads()
    if not threads:
        if user_id:
            await send_message_with_start_button(await bot.get_current().get_me(), "Список тем пуст.")
        return

    for thread in threads:
        thread_id = thread[0]
        result = bump_thread(thread_id)
        if user_id:
            await bot.send_message(user_id, result[1])
        await asyncio.sleep(5)