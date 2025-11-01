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
from aiogram.fsm.state import State, StatesGroup, default_state

redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)


router = Router()


class Form(StatesGroup):
    #Часть 1
    type_event = State()#Тип мероприятия
    event_date = State() #Дата проведения мероприятия
    venue = State()  #Место проведения
    num_guests = State()  #Количество гостей
    budget_event = State()  # Место проведения
    #Часть 2
    atmosphere = State()  #Какая будет атмосфера
    specific_topic = State()  # Есть ли конкретная тема мероприятия
    emotions_guests = State() #Какие эмоции вы хотите, чтобы гости испытали?
    key_poinst_or_traditions = State() #Есть ли ключевые моменты или традиции, которые обязательно должны быть включены?
    special_guests = State() #Есть ли гости, которых нужно особо выделить?
    #Промежуточная часть для "special_guests" для записи важных гостей
    add_guests = State() #Произведение записи важных гостей
    #Часть 3
    performances_artists = State() #Планируются ли выступления артистов?
    media = State() #Хотите ли вы включить видеопрезентации, слайд-шоу или другие медиа?
    time_programm = State() #Есть ли у вас пожелания по таймингу программы?
    #Часть 4
    responsible_for_the_event = State() #Кто отвечает за координацию мероприятия?
    all_time_event = State() #Какой тайминг у мероприятия?
    restrictions_of_the_site = State() #Есть ли ограничения на площадке?
    forbidden_at_the_event = State() #Есть ли что-то, чего вы категорически не хотите на мероприятии?
    #Часть 5
    dress_code = State() #Есть ли дресс-код для гостей или ведущего?
    contact_phone = State()


class DataEvent:
    def __init__(self):
        self.type = None #Тип мероприятия
        self.date = None #Дата проведения мероприятия
        self.venue = None #Место проведения
        self.budget_event = None #Бюджет мероприятия
        self.num_guests = None #Количество гостей
        self.atmosphere = None #Какая будет атмосфера
        self.specific_topic = None #сть ли конкретная тема мероприятия
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
        await message.answer(text='<b>Укажите бюджет мероприятия</b>\n '
                                  '<u>Зачем*:</u> Помогает понять, какие услуги и шоу-программы можно предложить, '
                                  'чтобы уложиться в финансовые рамки.', parse_mode=ParseMode.HTML)
    else:
        await message.answer(text='Вы ввели неправильный формат. Пожалуйста введите количество гостей согласно примеру.'
                                  '(Пример: 31)')
        return


@router.message(Form.budget_event)
async def add_budget(message: Message, state: FSMContext):
    await state.update_data(budget_event=message.text)
    await state.set_state(Form.atmosphere)
    await message.answer(text='<b>Какую атмосферу вы хотите создать?</b>\n'
                              '(веселую, трогательную, элегантную, неформальную и т.д. введите ответ в свободной форме)')


@router.message(Form.atmosphere)
async def add_atmosphere(message: Message, state: FSMContext):
    await state.update_data(atmosphere=message.text)
    await state.set_state(Form.specific_topic)
    await message.answer(text='<b>Часть 2: Цели и пожелания заказчика</b>\n\n'
                              '<b>Есть ли конкретная тема мероприятия?</b>\n'
                              '(например, свадьба в стиле "Гэтсби", корпоратив в морской тематике).\n'
                              '<u>*Зачем*:</u> Позволяет разработать уникальный сценарий, декор и активности, '
                              'соответствующие тематике.', parse_mode=ParseMode.HTML)


@router.message(Form.specific_topic)
async def add_specific_topic(message: Message, state: FSMContext):
    await state.update_data(specific_topic=message.text)
    await state.set_state(Form.emotions_guests)
    await message.answer(text='<b>Какие эмоции вы хотите, чтобы гости испытали?</b>\n'
                              '<u>*Зачем*:</u> Помогает выстроить сценарий так, чтобы он вызывал нужные эмоции '
                              '(радость, ностальгия, вдохновение). Напишите в свободной форме.',
                         parse_mode=ParseMode.HTML)


@router.message(Form.emotions_guests)
async def add_emotions_guests(message: Message, state: FSMContext):
    await state.update_data(emotions_guests=message.text)
    await state.set_state(Form.key_poinst_or_traditions)
    await message.answer(text='<b>Есть ли ключевые моменты или традиции, '
                              'которые обязательно должны быть включены?</b> (например, первый танец на свадьбе, вынос '
                              'торта, корпоративные награждения).\n'
                              'Напишите в свободной форме.', parse_mode=ParseMode.HTML)


@router.message(Form.key_poinst_or_traditions)
async def add_key_point_or_traditions(message: Message, state: FSMContext):
    await state.update_data(key_points_or_traditions=message.text)
    await state.set_state(Form.special_guests)
    await message.answer(text='<b>Есть ли гости, которых нужно особо выделить?</b> (например, почетные гости, '
                              'родственники, руководители). Напишите Да/Нет для продолжения.', parse_mode=ParseMode.HTML)


@router.message(Form.special_guests)
async def add_special_guests(message: Message, state: FSMContext):
    if message.text.lower() not in ['да', 'нет']:
        await message.answer(text='Пожалуйста введите один вариант из предложенных: Да/Нет')
        return
    if message.text.lower() == 'да':
        await state.update_data(list_special_guests=[])
        await message.answer(text='Введите ФИО гостя. Либо напишите "Закончить"')
        await state.set_state(Form.add_guests)
    else:
        await state.update_data(list_special_guests = message.text)
        await message.answer(text='Хорошо, продолжим!')
        await state.set_state(Form.performances_artists)
        await message.answer(text='<b>Часть 3:</b> Программа и развлечения\n\n'
                                  '<b>Планируются ли выступления артистов?</b>\n'
                                  '(музыканты, танцоры, шоу-программы).\n'
                                  '<u>*Зачем*:</u> Влияет на тайминг, '
                                  'техническое обеспечение и координацию с подрядчиками.\n'
                                  'Напишите в свободной форме.', parse_mode=ParseMode.HTML)


@router.message(Form.add_guests)
async def add_add_guests(message: Message, state: FSMContext):
    data = await state.get_data()
    list_special_guests = data.get('list_special_guests', [])

    if message.text.lower() == 'закончить':
        await message.answer(text=f'Вот все гости которых вы ввели: {list_special_guests}')
        await state.set_state(Form.performances_artists)
        await message.answer(text='<b>Планируются ли выступления артистов?</b>\n'
                                  '(музыканты, танцоры, шоу-программы).\n'
                                  '<u>*Зачем*:</u> Влияет на тайминг, '
                                  'техническое обеспечение и координацию с подрядчиками.\n'
                                  'Напишите в свободной форме.', parse_mode=ParseMode.HTML)
        return
    list_special_guests.append(message.text)
    await state.update_data(list_special_guests=list_special_guests)
    await message.answer(text='Записал! Введите следующее ФИО или напишите "Закончить"')


@router.message(Form.performances_artists)
async def add_performances_artists(message: Message, state: FSMContext):
    await state.update_data(performances_artists=message.text)
    await state.set_state(Form.media)
    await message.answer(text='<b>Хотите ли вы включить видеопрезентации, слайд-шоу или другие медиа?</b>\n'
                              '<u>*Зачем*:</u> Требует подготовки оборудования (проектор, экран) и контента.\n'
                              'Введите Да/Нет',
                         parse_mode=ParseMode.HTML)


@router.message(Form.media)
async def add_media(message: Message, state: FSMContext):
    if message.text.lower() not in ['да', 'нет']:
        await message.answer(text='Вы ввели не по шаблону, введите "Да/Нет"')
        return
    await state.update_data(media=message.text)
    await state.set_state(Form.time_programm)
    await message.answer(text='<b>Есть ли у вас пожелания по таймингу программы?</b>\n'
                              '(например, короткие тосты, длинные танцевальные блоки).\n'
                              '<u>*Зачем*:</u> Помогает выстроить сценарий с учетом ритма мероприятия.\n\n'
                              'Напишите в свободной форме',
                         parse_mode=ParseMode.HTML)


@router.message(Form.time_programm)
async def add_time_programm(message: Message, state: FSMContext):
    await state.update_data(time_programm=message.text)
    await state.set_state(Form.responsible_for_the_event)
    await message.answer(text='<b>Часть 4:</b> Организационные детали\n\n'
                              '<b>Кто отвечает за координацию мероприятия?</b>\n'
                              '(сам заказчик, организатор).\n'
                              '<u>*Зачем*:</u> Позволяет понять, с кем взаимодействовать по организационным вопросам.',
                         reply_markup=keyboards.responsible_for_the_event_kb, parse_mode=ParseMode.HTML)


@router.message(Form.responsible_for_the_event)
async def add_responsible_for_the_event(message: Message, state: FSMContext):
    if message.text.lower() not in ['сам заказчик', 'организатор']:
        await message.answer(text='Пожалуйста нажмите на одну из кнопок')
        return
    await state.update_data(responsible_for_the_event=message.text)
    await state.set_state(Form.all_time_event)
    await message.answer(text='<b>Сколько всего времени будет длиться мероприятие?</b>\n'
                              'Укажите в часах. <u>Пример: 8</u>', parse_mode=ParseMode.HTML)


@router.message(Form.all_time_event)
async def add_all_time_event(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(text='Вы ввели не по примеру, повторите попытку')
        return
    await state.update_data(all_time_event=message.text)
    await state.set_state(Form.restrictions_of_the_site)
    await message.answer(text='<b>Есть ли ограничения на площадке?</b>\n'
                              '(например, запрет на громкую музыку после 22:00).\n'
                              '<u>*Зачем*:</u> Избегает непредвиденных ситуаций и конфликтов с администрацией.\n'
                              'Напишите в свободной форме', parse_mode=ParseMode.HTML)


@router.message(Form.restrictions_of_the_site)
async def add_restrictions_of_the_site(message: Message, state: FSMContext):
    await state.update_data(restrictions_of_the_site=message.text)
    await state.set_state(Form.forbidden_at_the_event)
    await message.answer(text='<b>Есть ли что-то, чего вы категорически не хотите на мероприятии?</b>\n'
                              '(например, определенные конкурсы, шутки на чувствительные темы).\n'
                              '<u>*Зачем*:</u> Избегает неловких ситуаций и конфликтов.\n'
                              'Напишите в свободной форме.', parse_mode=ParseMode.HTML)


@router.message(Form.forbidden_at_the_event)
async def add_forbidden_at_the_event(message: Message, state: FSMContext):
    await state.update_data(forbidden_at_the_event=message.text)
    await state.set_state(Form.dress_code)
    await message.answer(text='<b>Часть 5:</b> Дополнительные детали\n\n'
                              '<b>Есть ли дресс-код для гостей или ведущего?</b>\n'
                              '<u>*Зачем*:</u> Позволяет ведущему соответствовать стилю мероприятия.\n'
                              'Напишите в свободной форме', parse_mode=ParseMode.HTML)


@router.message(Form.dress_code)
async def add_dress_code(message: Message, state: FSMContext):
    await state.update_data(dress_code=message.text)
    await state.set_state(Form.contact_phone)
    await message.answer(text='<b>Последний шаг</b> - введите <b>номер телефона</b> для того чтобы '
                              'я смог с вами связаться в <u>формате: 8-999-888-77-66</u>', parse_mode=ParseMode.HTML)


@router.message(Form.contact_phone)
async def add_contact_phone(message: Message, state: FSMContext):
    if re.search(r'^\d{1}-\d{3}-\d{3}-\d{2}-\d{2}$', message.text):
        await state.update_data(contact_phone=message.text)
        admin_id = 498037596
        if message.from_user.id == admin_id:
            await message.answer(text='<b>Поздравляю, мы создали с вами событие!</b>', parse_mode=ParseMode.HTML,
                                 reply_markup=keyboards.main_admin_kb)
        else:
            await message.answer(text='<b>Поздравляю, мы создали с вами событие!</b>', parse_mode=ParseMode.HTML,
                                 reply_markup=keyboards.main_user_kb)
        data = await state.get_data()

        id_user = message.from_user.id
        user_key = f'user:{id_user}'


        user_count_event = redis_client.hlen(user_key)
        user_event_key = f'event:{user_count_event}'

        event_data = {
            "type_event": data["type_event"],
            "event_date": data["event_date"],
            "venue": data["venue"],
            "num_guests": data["num_guests"],
            "budget_event": data["budget_event"],
            "atmosphere": data["atmosphere"],
            "specific_topic": data["specific_topic"],
            "emotions_guests": data["emotions_guests"],
            "key_poinst_or_traditions": data["key_points_or_traditions"],
            "special_guests": data["list_special_guests"],
            "performances_artists": data["performances_artists"],
            "media": data["media"],
            "time_programm": data["time_programm"],
            "responsible_for_the_event": data["responsible_for_the_event"],
            "all_time_event": data["all_time_event"],
            "restrictions_of_the_site": data["restrictions_of_the_site"],
            "forbidden_at_the_event": data["forbidden_at_the_event"],
            "dress_code": data["dress_code"],
            "contact_phone": data["contact_phone"]
        }

        redis_client.hset(user_key, user_event_key, json.dumps(event_data, ensure_ascii=False))


        event_text = (f"<b>Мероприятие создано!</b>\n"
                      "Часть 1: Общая информация о мероприятии."
                      f"<b>Тип:</b> {data['type_event']}\n"
                      f"<b>Дата:</b> {data['event_date']}\n"
                      f"<b>Место проведения:</b> {data['venue']}\n"
                      f"<b>Количество гостей:</b> {data['num_guests']}\n"
                      f"<b>Бюджет мероприятия:</b> {data['budget_event']}\n"
                      "Часть 2. Цели и пожелания заказчика."
                      f"<b>Какую атмосферу вы хотите создать:</b> {data['atmosphere']}\n"
                      f"<b>Конкретная тема или концепция мероприятия</b> {data['specific_topic']}\n"
                      f"<b>Какие эмоции вы хотите, чтобы гости испытали?</b> {data['emotions_guests']}\n"
                      f"<b>Ключевые моменты или традиции, "
                      f"которые обязательно должны быть включены?</b> {data['key_points_or_traditions']}\n"
                      f"<b>Гости, которых нужно особо выделить:</b> {data['list_special_guests']}\n"
                      "Часть 3. Программа и развлечения"
                      f"<b>Планируются ли выступления артистов?</b> {data['performances_artists']}\n"
                      f"<b>Хотите ли вы включить видеопрезентации, слайд-шоу или другие медиа?</b> {data['media']}\n"
                      f"<b> Есть ли у вас пожелания по таймингу программы?</b> {data['time_programm']}\n"
                      "Часть 4. Организационные детали."
                      f"<b>Кто отвечает за координацию мероприятия?</b> {data['responsible_for_the_event']}\n"
                      f"<b>Какой тайминг у мероприятия? В часах:</b> {data['all_time_event']}\n"
                      f"<b>Есть ли ограничения на площадке?</b> {data['restrictions_of_the_site']}\n"
                      f"<b>Есть ли что-то, чего вы категорически не хотите на мероприятии?</b> "
                      f"{data['forbidden_at_the_event']}\n"
                      f"<b>Есть ли дресс-код для гостей или ведущего?</b> {data['dress_code']}\n"
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
                info.append(f'{event_data_for_admin['type_event']}, дата: {event_data_for_admin['event_date']}')

        await message.answer(text='Выберите мероприятие:', reply_markup=keyboards.get_all_events_kb(info, real_keys))


    else:
        id_user = f'user:{message.from_user.id}'
        events = redis_client.hgetall(id_user)
        keys = redis_client.hkeys(id_user)
        info = []
        for key, value in (events.items()):
            event_data = json.loads(value)
            info.append(f'{event_data['type_event']}, дата: {event_data['event_date']}')

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
    data = json.loads(redis_client.hget(f'user:{id_user}', event_key))

    responses = (f"<b>Мероприятие создано!</b>\n"
                      "Часть 1: Общая информация о мероприятии."
                      f"<b>Тип:</b> {data['type_event']}\n"
                      f"<b>Дата:</b> {data['event_date']}\n"
                      f"<b>Место проведения:</b> {data['venue']}\n"
                      f"<b>Количество гостей:</b> {data['num_guests']}\n"
                      f"<b>Бюджет мероприятия:</b> {data['budget_event']}\n"
                      "Часть 2. Цели и пожелания заказчика."
                      f"<b>Какую атмосферу вы хотите создать:</b> {data['atmosphere']}\n"
                      f"<b>Конкретная тема или концепция мероприятия</b> {data['specific_topic']}\n"
                      f"<b>Какие эмоции вы хотите, чтобы гости испытали?</b> {data['emotions_guests']}\n"
                      f"<b>Ключевые моменты или традиции, "
                      f"которые обязательно должны быть включены?</b> {data['key_poinst_or_traditions']}\n"
                      f"<b>Гости, которых нужно особо выделить:</b> {data['special_guests']}\n"
                      "Часть 3. Программа и развлечения"
                      f"<b>Планируются ли выступления артистов?</b> {data['performances_artists']}\n"
                      f"<b>Хотите ли вы включить видеопрезентации, слайд-шоу или другие медиа?</b> {data['media']}\n"
                      f"<b> Есть ли у вас пожелания по таймингу программы?</b> {data['time_programm']}\n"
                      "Часть 4. Организационные детали."
                      f"<b>Кто отвечает за координацию мероприятия?</b> {data['responsible_for_the_event']}\n"
                      f"<b>Какой тайминг у мероприятия? В часах:</b> {data['all_time_event']}\n"
                      f"<b>Есть ли ограничения на площадке?</b> {data['restrictions_of_the_site']}\n"
                      f"<b>Есть ли что-то, чего вы категорически не хотите на мероприятии?</b> "
                      f"{data['forbidden_at_the_event']}\n"
                      f"<b>Есть ли дресс-код для гостей или ведущего?</b> {data['dress_code']}\n"
                      f"<b>Телефон:</b> {data['contact_phone']}")


    await callback.message.answer(text=f'<b>Ваше мероприятие:</b> \n{responses}', parse_mode=ParseMode.HTML)
    await callback.answer()

