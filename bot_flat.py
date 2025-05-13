from typing import Union

from aiogram import Bot, Dispatcher, types, F
import asyncio
import logging
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from config_reader import config
import bd_flats

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()
class UserState(StatesGroup):
    city = State()
    address = State()
    description = State()
    photo = State()
    price = State()
    contacts = State()

class CostState(StatesGroup):
    more = State()
    less = State()

class CityState(StatesGroup):
    city = State()


async def setup_bot_commands():
    bot_commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/repost", description="Выставить квартиру"),
        BotCommand(command="/find", description="Найти квартиру"),
        BotCommand(command="/help", description="Помощь по командам"),
    ]
    await bot.set_my_commands(bot_commands)


@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    buttons = [
        [InlineKeyboardButton(text="Основные команды", callback_data="help_main")],
        [InlineKeyboardButton(text="Поиск квартир", callback_data="help_search")],
        [InlineKeyboardButton(text="Размещение объявлений", callback_data="help_post")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите раздел помощи:", reply_markup=kb)


@dp.callback_query(F.data.startswith("help_"))
async def help_sections(call: types.CallbackQuery):
    section = call.data.split("_")[1]
    text = ""

    if section == "main":
        text = "<b>Основные команды:</b>\n\n" \
               "<code>/start</code> - Главное меню\n" \
               "<code>/help</code> - Помощь по командам\n" \

    elif section == "search":
        text = "<b>Поиск квартир:</b>\n\n" \
               "<code>/find</code> - Найти квартиру\n" \
               "Используйте эту команду для поиска арендных квартир"

    elif section == "post":
        text = "<b>Размещение объявлений:</b>\n\n" \
               "<code>/repost</code> - Выставить квартиру\n" \
               "Используйте эту команду для размещения объявления"

    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    buttons = [
        [InlineKeyboardButton(text='Я хочу ВЫСТАВИТЬ арендную квартиру', callback_data='repost')],
        [InlineKeyboardButton(text='Я хочу НАЙТИ арендную квартиру', callback_data='find')],
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer('Привет! Я бот помогающий тебе найти или выставить арендную квартиру!', reply_markup=kb)
    await message.delete()

async def find_handler(message_or_call: Union[types.Message, types.CallbackQuery]):
    if isinstance(message_or_call, types.CallbackQuery):
        await message_or_call.answer()
        await message_or_call.message.edit_reply_markup(reply_markup=None)
        message = message_or_call.message
    else:
        message = message_or_call

    buttons = [
        [InlineKeyboardButton(text='По стоимости', callback_data='cost')],
        [InlineKeyboardButton(text='По городу', callback_data='city')],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer('По какому параметру будем искать квартиру?', reply_markup=kb)

@dp.callback_query(F.data == 'find')
async def repost_callback(call: types.CallbackQuery):
    """Обработчик кнопки 'repost'"""
    await find_handler(call)


@dp.message(Command('find'))
async def repost_command(message: types.Message):
    """Обработчик команды /repost"""
    await find_handler(message)


async def repost_handler(message_or_call: Union[types.Message, types.CallbackQuery], state: FSMContext):
    if isinstance(message_or_call, types.CallbackQuery):
        await message_or_call.answer()
        await message_or_call.message.edit_reply_markup(reply_markup=None)
        message = message_or_call.message
    else:
        message = message_or_call

    await state.clear()
    await message.answer('Введите город')
    await state.set_state(UserState.city)


@dp.callback_query(F.data == 'repost')
async def repost_callback(call: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'repost'"""
    await repost_handler(call, state)


@dp.message(Command('repost'))
async def repost_command(message: types.Message, state: FSMContext):
    """Обработчик команды /repost"""
    await repost_handler(message, state)

@dp.message(UserState.city)
async def numb_flat(message, state):
    await state.update_data(city=message.text)
    await message.answer('Введите адрес квартиры')
    await state.set_state(UserState.address)


@dp.message(UserState.address)
async def set_address(message, state):
    await state.update_data(address= message.text)
    await message.answer('Опишите квартиру')
    await state.set_state(UserState.description)

@dp.message(UserState.description)
async def set_descript(message:types.Message, state: FSMContext):
    await state.update_data(description= message.text)
    await message.answer('Прикрепите фото: ')
    await state.set_state(UserState.photo)


@dp.message(UserState.photo, F.photo | F.document)  # Обрабатываем и фото, и файлы
async def set_photo(message: types.Message, state: FSMContext):
    photo_id = None
    is_document = False

    # Если это фото (отправлено как изображение)
    if message.photo:
        photo_id = message.photo[-1].file_id  # Берем последнее (самое качественное) фото
        logging.info(f"Получено фото (изображение): {photo_id}")

    # Если это файл (отправлено как документ)
    elif message.document and message.document.mime_type.startswith('image/'):
        photo_id = message.document.file_id
        is_document = True
        logging.info(f"Получено фото (файл): {photo_id}")

    # Если фото или файл с изображением успешно обработаны
    if photo_id:
        await state.update_data(photo=photo_id, is_document=is_document)
        await message.answer("Оставьте контакты для обратной связи.")
        await state.set_state(UserState.contacts)
    else:
        await message.answer("Пожалуйста, отправьте фото в формате изображения или файла.")

    await message.delete()


# Обработчик для случаев, когда пользователь отправляет что-то кроме фото
@dp.message(UserState.photo)
async def handle_non_photo(message: types.Message):
    await message.answer("Пожалуйста, отправьте фото.")

@dp.message(UserState.contacts)
async def set_contacts(message, state):
    await state.update_data(contacts= message.text)
    await message.answer('Введите цену (в месяц, руб)')
    await state.set_state(UserState.price)

@dp.message(UserState.price)
async def set_price(message, state):
    buttons = [
        [InlineKeyboardButton(text='Да', callback_data='ok')],
        [InlineKeyboardButton(text='Нет', callback_data='repost')],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.update_data(price= int(message.text))
    data = await state.get_data()

    if data['is_document'] == False:
        await message.answer_photo(
            photo=data['photo'],  # file_id фото
            caption=f"Итоговый результат:\nГород: {data['city']}\nАдрес: {data['address']}\nОписание: {data['description']}"
                    f"\nКонтакты: {data['contacts']}\nЦена: {data['price']} руб.\n\nВсё верно?",
            reply_markup=kb
        )
    else:
        await message.answer_document(
            document=data['photo'],  # file_id фото
            caption=f"Итоговый результат:\nГород: {data['city']}\nАдрес: {data['address']}\nОписание: {data['description']}"
                    f"\nКонтакты: {data['contacts']}\nЦена: {data['price']} руб.\n\nВсё верно?",
            reply_markup=kb
        )

    bd_flats.insert_flat(data['city'].lower(), data['address'], data['description'], data['photo'], data['contacts'], data['price'])



@dp.callback_query(F.data == 'ok')  # Обработчик для кнопки "Да"
async def handle_ok_button(call: types.CallbackQuery):
    # Отвечаем на callback (убираем "часики" на кнопке)
    await call.answer()

    # Убираем клавиатуру "Да" и "Нет", редактируя сообщение
    await call.message.edit_reply_markup(reply_markup=None)

    # Создаем новую клавиатуру с кнопкой "Вернуться в начало"
    back_to_start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вернуться в начало", callback_data="back_to_start")]
        ]
    )

    # Отправляем сообщение с новой клавиатурой
    await call.message.answer("Квартира успешно добавлена!", reply_markup=back_to_start_keyboard)


@dp.callback_query(F.data == 'back_to_start')  # Обработчик для кнопки "Вернуться в начало"
async def handle_back_to_start(call: types.CallbackQuery):
    # Отвечаем на callback
    await call.answer()

    # Вызываем команду /start
    await cmd_start(call.message)


@dp.callback_query(F.data == 'city')
async def check_by_cost(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('Введите город для поиска')
    await call.answer()
    await state.set_state(CityState.city)

@dp.message(CityState.city)
async def cost_check_more(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(city=message.text)
    data = await state.get_data()
    true_flats = bd_flats.check_by_city(data['city'])
    if true_flats == 0:
        buttons = [
            [InlineKeyboardButton(text='Ещё раз', callback_data='find')],
            [InlineKeyboardButton(text='На главную', callback_data='back_to_start')],
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Нет квартир, подходящих под ваш запрос', reply_markup=kb)
    else:
        for flat in true_flats:
            try:
                await message.answer_photo(
                    photo=flat[3],
                    caption=f"Город: {flat[0].title()}\nАдрес: {flat[1]}\nОписание: {flat[2]}"
                            f"\nКонтакты: {flat[4]}\nЦена: {flat[5]} руб."
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке фото: {e}")
                await message.answer_document(
                    document=flat[3],
                    caption=f"Город: {flat[0].title()}\nАдрес: {flat[1]}\nОписание: {flat[2]}"
                            f"\nКонтакты: {flat[4]}\nЦена: {flat[5]} руб."
                )
        buttons = [
            [InlineKeyboardButton(text='Ещё раз', callback_data='find')],
            [InlineKeyboardButton(text='На главную', callback_data='back_to_start')],
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Следующие действия', reply_markup=kb)

    await state.clear()


@dp.callback_query(F.data == 'cost')
async def check_by_cost(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    buttons = [
        [InlineKeyboardButton(text='Больше названной стоимости', callback_data='more')],
        [InlineKeyboardButton(text='Меньше названной стоимости', callback_data='less')],
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.answer('Выберите условие отбора квартиры по стоимости', reply_markup=kb)

@dp.callback_query(F.data == 'more')
async def check_by_cost_more(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Введите стоимость, от которой следует начать (Больше), руб./мес.')
    await call.answer()
    await state.set_state(CostState.more)

@dp.message(CostState.more)
async def cost_check_more(message: types.Message, state: FSMContext):
    await state.update_data(more=int(message.text))
    data = await state.get_data()
    true_flats = bd_flats.check_by_cost_more(data['more'])
    if true_flats == 0:
        buttons = [
            [InlineKeyboardButton(text='Ещё раз', callback_data='find')],
            [InlineKeyboardButton(text='На главную', callback_data='back_to_start')],
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Нет квартир, подходящих под ваш запрос', reply_markup=kb)
    else:
        for flat in true_flats:
            try:
                await message.answer_photo(
                    photo=flat[3],
                    caption=f"Город: {flat[0].title()}\nАдрес: {flat[1]}\nОписание: {flat[2]}"
                            f"\nКонтакты: {flat[4]}\nЦена: {flat[5]} руб."
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке фото: {e}")
                await message.answer_document(
                    document=flat[3],
                    caption=f"Город: {flat[0].title()}\nАдрес: {flat[1]}\nОписание: {flat[2]}"
                            f"\nКонтакты: {flat[4]}\nЦена: {flat[5]} руб."
                )

        buttons = [
            [InlineKeyboardButton(text='Ещё раз', callback_data='find')],
            [InlineKeyboardButton(text='На главную', callback_data='back_to_start')],
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Следующие действия', reply_markup=kb)

    await state.clear()


@dp.callback_query(F.data == 'less')
async def check_by_cost_less(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('Введите стоимость, от которой следует начать (Меньше), руб./мес.')
    await call.answer()
    await state.set_state(CostState.less)

@dp.message(CostState.less)
async def cost_check_less(message: types.Message, state: FSMContext):
    await state.update_data(less=int(message.text))
    data = await state.get_data()
    true_flats = bd_flats.check_by_cost_less(data['less'])

    if true_flats == 0:
        buttons = [
            [InlineKeyboardButton(text='Ещё раз', callback_data='find')],
            [InlineKeyboardButton(text='На главную', callback_data='back_to_start')],
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Нет квартир, подходящих под ваш запрос', reply_markup=kb)
    else:
        for flat in true_flats:
            try:
                await message.answer_photo(
                    photo=flat[3],
                    caption=f"Город: {flat[0].title()}\nАдрес: {flat[1]}\nОписание: {flat[2]}"
                            f"\nКонтакты: {flat[4]}\nЦена: {flat[5]} руб."
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке фото: {e}")
                await message.answer_document(
                    document=flat[3],
                    caption=f"Город: {flat[0].title()}\nАдрес: {flat[1]}\nОписание: {flat[2]}"
                            f"\nКонтакты: {flat[4]}\nЦена: {flat[5]} руб."
                )
        buttons = [
            [InlineKeyboardButton(text='Ещё раз', callback_data='find')],
            [InlineKeyboardButton(text='На главную', callback_data='back_to_start')],
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Следующие действия', reply_markup=kb)

    await state.clear()


async def main():
    await setup_bot_commands()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())