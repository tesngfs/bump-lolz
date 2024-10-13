from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils import send_message_with_main_menu, send_message_with_start_button, bump_all_threads, get_all_threads, add_thread_to_db, delete_thread_from_db, get_thread_title
from config import IMG_URL
import asyncio
import logging

router = Router()

class AddThreadState(StatesGroup):
    waiting_for_thread_ids = State()

@router.callback_query(F.data == 'main_menu')
async def process_main_menu_callback(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()  
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    await callback_query.answer()

@router.callback_query(F.data == 'start')
async def process_start_callback(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete() 
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    await callback_query.answer()
    await send_welcome(callback_query.message)

@router.callback_query(F.data == 'add_thread')
async def process_add_callback(callback_query: CallbackQuery, state: FSMContext, bot):
    try:
        await callback_query.message.delete() 
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    user_id = callback_query.from_user.id
    await bot.send_message(chat_id=user_id, text="Введите ID тем через запятую для добавления:")
    await state.set_state(AddThreadState.waiting_for_thread_ids)

@router.message(AddThreadState.waiting_for_thread_ids)
async def add_threads(message: Message, state: FSMContext):
    thread_ids = message.text.split(',')
    added_threads = []
    for thread_id in thread_ids:
        thread_id = thread_id.strip()
        if thread_id.isdigit():
            if add_thread_to_db(thread_id):
                added_threads.append(thread_id)
            else:
                await message.reply(f"Тема с ID {thread_id} уже есть в списке.")
    if added_threads:
        await send_message_with_start_button(message, f"Добавлены темы с ID: {', '.join(added_threads)}")
    else:
        await send_message_with_start_button(message, "Не удалось добавить темы. Убедитесь, что вы ввели корректные ID через запятую.")
    await state.clear()
    await message.delete()  

@router.callback_query(F.data == 'delete_thread')
async def process_delete_callback(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()  
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    await callback_query.answer()
    threads = get_all_threads()
    if not threads:
        await send_message_with_start_button(callback_query.message, "Список тем пуст.")
        return
    builder = InlineKeyboardBuilder()
    for thread in threads:
        builder.button(text=thread[0], callback_data=f'delete_{thread[0]}')
    builder.adjust(1)
    await callback_query.message.answer("Выберите тему для удаления:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith('delete_'))
async def process_delete_thread_callback(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete() 
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    thread_id = callback_query.data.split('_')[1]
    delete_thread_from_db(thread_id)
    await send_message_with_start_button(callback_query.message, f"Тема {thread_id} удалена.")
    threads = get_all_threads()
    if threads:
        await process_delete_callback(callback_query)
    else:
        await send_message_with_start_button(callback_query.message, "Список тем пуст.")

@router.callback_query(F.data == 'list_threads')
async def process_list_callback(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()  
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    threads = get_all_threads()
    if threads:
        thread_info = []
        for thread in threads:
            thread_id = thread[0]
            thread_title = await asyncio.to_thread(get_thread_title, thread_id)
            thread_link = f"<code>{thread_id}</code> - {thread_title} (<a href='https://zelenka.guru/threads/{thread_id}'>Перейти</a>)"
            thread_info.append(thread_link)
            await asyncio.sleep(3)
        await send_message_with_start_button(callback_query.message, "Список тем:\n" + "\n".join(thread_info), parse_mode='HTML')
    else:
        await send_message_with_start_button(callback_query.message, "Список тем пуст.")

@router.callback_query(F.data == 'bump_threads')
async def process_bump_callback(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete() 
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    await callback_query.answer()
    await bump_all_threads(callback_query.from_user.id)

@router.message(Command("start"))
async def send_welcome(message: Message):
    try:
        await message.delete()  
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
    builder = InlineKeyboardBuilder()
    builder.button(text="Темы", callback_data='list_threads')
    builder.button(text="Добавить тему", callback_data='add_thread')
    builder.button(text="Удалить тему", callback_data='delete_thread')
    builder.button(text="Поднять темы", callback_data='bump_threads')
    builder.adjust(3)
    await message.answer_photo(IMG_URL, caption="Привет! Я бот для поднятия тем. Выбери действие:",
                               reply_markup=builder.as_markup())