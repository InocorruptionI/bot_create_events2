from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router

router = Router()


main_admin_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Просмотреть мои мероприятия')],
                                              [KeyboardButton(text='Создать мероприятие')],
                                              [KeyboardButton(text='Архив')]],
                                    resize_keyboard=True)

main_user_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Создать мероприятие')],
                                             [KeyboardButton(text='Просмотреть мои мероприятия')]],
                                   resize_keyboard=True)


def get_events_keys(keys_events,real_key):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[], row_width=2)
    for key in range(len(keys_events)):
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=keys_events[key],
                                                              callback_data=real_key[key])])
    return keyboard


def get_all_events_kb(keys_events, real_key):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[], row_width=2)
    for key in range(len(keys_events)):
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=keys_events[key],
                                                              callback_data=real_key[key])])
    return keyboard


responsible_for_the_event_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Сам заказчик'),
                                                              KeyboardButton(text='Организатор')]])