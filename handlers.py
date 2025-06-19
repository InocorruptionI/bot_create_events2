import html
import re

from aiogram.enums import ParseMode
from redis import Redis
import json

import keyboards

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, User, ReplyKeyboardRemove

from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)


router = Router()


class Form(StatesGroup):
    type_event = State()#Тип мероприятия
    event_date = State() #Дата проведения мероприятия
    venue = State()  #Место проведения
    num_guests = State()  #Количество гостей
    budget_event = State()  # Место проведения
    atmosphere = State()  #Какая будет атмосфера
    specific_topic = State()  # Есть ли конкретная тема мероприятия
    event_info = State()
    contact_phone = State()


class DataEvent:
    def __init__(self):
        self.type = None #Тип мероприятия
        self.date = None #Дата проведения мероприятия
        self.venue = None #Место проведения
        self.budget_event = None #Бюджет мероприятия
        self.num_guests = None #Количество гостей
        self.atmosphere = None #Какая будет атмосфера
        self.specific_topic = None #Есть ли конкретная тема мероприятия
        self.info = None
        self.phone = None


@router.message(CommandStart())
async def start(message: Message):
    #Данная функция представляет собой приветствие для разных типов пользователей:
    #для администраторов и обычных пользователей
    admin_id = 498037596
    if message.from_user.id == admin_id:
        await message.answer(text='Привет Администратор! \n\n Выбери действие.', reply_markup=keyboards.main_admin_kb)
    else:
        await message.answer(text="Приветствую тебя дорогой пользователь!\n"
                                  "Этот бот предназначен для формирования заявок на мероприятия\n"
                                  "Давай наконец приступим созданию заявки!", reply_markup=keyboards.main_user_kb)


@router.message(F.text == 'Создать мероприятие')
async def create_event(message: Message, state: FSMContext) -> None:
    await state.update_data()
    await state.set_state(Form.type_event)
    await message.answer(text='<b>Часть 1. Общая информация о мероприятии:</b> \n'
                              'Какой тип мероприятия планируется? (Свадьба, Корпоратив, Юбилей, День рождения)\n'
                              '*Зачем*: Определяет стиль ведения, тон мероприятия\n'
                              '(формальный, неформальный, торжественный) и общую атмосферу. ',
                         reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)


@router.message(Form.type_event)
async def add_event_type(message: Message, state: FSMContext) -> None:
    walid_types = ['свадьба', 'день рождения', 'корпоратив', 'юбилей']
    if message.text.lower() not in walid_types:
        await message.answer(text='Ваш вариант не подходит ни под один из предложенных. Пожалуйста выберите '
                                  'тип из предложенных: '
                                  'Свадьба, День рождения, Корпоратив')
        return
    else:
        await state.update_data(type_event=message.text)
        await state.set_state(Form.event_date)
        await message.answer(text=f'Отлично! Мы начали создание мероприятия "{html.escape(message.text)}"! Едем дальше,'
                                  f'Дата и время проведения? В формате ГГГГ-ММ-ДД')


@router.message(Form.event_date)
async def add_event_date(message: Message, state: FSMContext):
    try:
        year, month, day = list(map(int, message.text.split('-')))
        valid_str = message.text.replace('-', '').isdigit()
        valid_len = message.text.replace('-', '')
        if not valid_str and not re.search(r'^\d{4}-\d{2}-\d{2}$', message.text) or \
                datetime.now() >= datetime(year, month, day):
            await message.answer(text='Что-то тут вы ввели не так, пробуем еще раз! Пример: ГГГГ-ММ-ДД')
            return

        await state.update_data(event_date=message.text)
        await state.set_state(Form.venue)
        await message.answer(text='<b>Укажите место проведения:</b> (ресторан, открытая площадка, '
                                    'загородный дом и т.д. в свободной форме)\n\n'
                                    '<u>*Зачем*:</u> Влияет на технические аспекты (звук, свет, сцена), логистику и '
                                    'взаимодействие с персоналом площадки.', parse_mode=ParseMode.HTML)
    except ValueError:
        await message.answer(text='Что-то тут вы ввели не так, давайте попробуем еще раз! Пример: ГГГГ-ММ-ДД')
        return


@router.message(Form.venue)
async def add_venue(message: Message, state: FSMContext):
    await state.update_data(venue=message.text)
    await state.set_state(Form.num_guests)
    await message.answer(text='<b>Укажите количество гостей</b>\n\n'
                              '<u>*Зачем*</u>: Определяет масштаб мероприятия, выбор активностей, '
                              'количество необходимых ресурсов (например, микрофонов, мест для рассадки).',
                         parse_mode=ParseMode.HTML)

@router.message(Form.num_guests)
async def add_num_guests(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(num_guests=int(message.text))
        await state.set_state(Form.budget_event)
        await message.answer(text='Укажите бюджет мероприятия\n '
                                  'Зачем*: Помогает понять, какие услуги и шоу-программы можно предложить, '
                                  'чтобы уложиться в финансовые рамки.')
    else:
        await message.answer(text='Вы ввели неправильный формат. Пожалуйста введите количество гостей согласно примеру.'
                                  '(Пример: 31)')
        return


@router.message(Form.budget_event)
async def add_budget(message: Message, state: FSMContext):
    await state.update_data(budget_event=message.text)
    await state.set_state(Form.atmosphere)
    await message.answer(text='Какую атмосферу вы хотите создать?')


@router.message(Form.event_info)
async def add_info(message: Message, state: FSMContext):
    test_check = ['Формат:', 'Имена гостей:', 'Мелочи:']
    for check in test_check:
        if check not in message.text:
            await message.answer(text='Вы ввели не по шаблону. Пожалуйста введите текст по примеру. \n'
                                      'Пример: Формат: текст \n'
                                      'Имена гостей: текст\n'
                                      'Мелочи: текст')
            return
    await state.update_data(event_info=message.text)
    await state.set_state(Form.contact_phone)
    await message.answer(text='Отлично, я записал ваш текст. Последний шаг - введите номер телефона для того чтобы '
                              'я смог с вами связаться в формате: 8-999-888-77-66')


@router.message(Form.contact_phone)
async def add_contact_phone(message: Message, state: FSMContext):
    if re.search(r'^\d{1}-\d{3}-\d{3}-\d{2}-\d{2}$', message.text):
        await state.update_data(contact_phone=message.text)
        await message.answer(text='Поздравляю, мы создали с вами событие!')
        data = await state.get_data()

        id_user = message.from_user.id
        user_key = f'user:{id_user}'


        user_count_event = redis_client.hlen(user_key)
        user_event_key = f'event:{user_count_event}'

        event_data = {
            "type": data["type_event"],
            "date": data["event_date"],
            "num_guests": data["num_guests"],
            "event_info": data["event_info"],
            "telephone": data["contact_phone"]
        }

        redis_client.hset(user_key, user_event_key, json.dumps(event_data, ensure_ascii=False))


        event_text = (f"<b>Мероприятие создано!</b>\n"
                      f"<b>Тип:</b> {data['type_event']}\n"
                      f"<b>Дата:</b> {data['event_date']}\n"
                      f"<b>Гостей:</b> {data['num_guests']}\n"
                      f"<b>Информация:</b> {data['event_info']}\n"
                      f"<b>Телефон:</b> {data['contact_phone']}")
        id_admin = 498037596
        if id_admin == message.from_user.id:
            await message.answer(text=event_text, reply_markup=keyboards.main_admin_kb, parse_mode=ParseMode.HTML)
        else:
            await message.answer(text=event_text, reply_markup=keyboards.main_user_kb, parse_mode=ParseMode.HTML)

        await state.clear()
    else:
        await message.answer(text='Что-то вы ввели тут не так, давайте попробуем еще раз по примеру: 8-999-888-77-66')
        return


@router.message(F.text == 'Просмотреть мои мероприятия')
async def check_keys_events(message: Message):
    admin_id =498037596
    if admin_id == message.from_user.id:
        name_users_in_db = redis_client.keys(memoryview='*')
        events_for_admin = []
        for name in name_users_in_db:
            events_for_admin.append(redis_client.hgetall(name))

        real_keys = []
        info = []
        for index in events_for_admin:
            for key, value in (index.items()):
                real_keys.append(key)
                event_data_for_admin = json.loads(value)
                info.append(f'{event_data_for_admin['type']}, дата: {event_data_for_admin['date']}')

        await message.answer(text='Выберите мероприятие:', reply_markup=keyboards.get_all_events_kb(info, real_keys))


    else:
        id_user = f'user:{message.from_user.id}'
        events = redis_client.hgetall(id_user)
        keys = redis_client.hkeys(id_user)
        info = []
        for key, value in (events.items()):
            event_data = json.loads(value)
            info.append(f'{event_data['type']}, дата: {event_data['date']}')

        if not keys:
            await message.answer(text='У вас еще нет мероприятий')
            return
        else:
            await message.answer(text='Выберите мероприятие:', reply_markup=keyboards.get_events_keys(info, real_key=keys))



@router.callback_query()
async def info_key_for_user(callback: CallbackQuery):
    #Здесь в этой функции мы выводим информацию о выбранном мероприятии
    event_key = callback.data # берем ключ вручную
    id_user = callback.from_user.id # id юзера
    event_info = json.loads(redis_client.hget(f'user:{id_user}', event_key))

    responses = (f'<b>Тип мероприятия:</b> {event_info['type']}\n'
                 f'<b>Дата проведения:</b> {event_info['date']}\n'
                 f'<b>Количество гостей:</b> {event_info['num_guests']}\n'
                 f'<b>Информация о мероприятии:</b> {event_info['event_info']}\n'
                 f'<b>Номер телефона:</b> {event_info['telephone']}\n\n'
    )


    await callback.message.answer(text=f'<b>Ваше мероприятие:</b> \n{responses}', parse_mode=ParseMode.HTML)
    await callback.answer()

