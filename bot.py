import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from sqlither import SQLighther

from stopgame import StopGame


# Задаем уровень логов
logging.basicConfig(level=logging.INFO)

# Инициализируем бота
bot = Bot('TOKEN')
dp = Dispatcher(bot)

# Инициализируем соезинение с БД
db = SQLighther('db.db')

# Инициализируем парсер
sg = StopGame('lastkey.txt')

# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    if(not db.subscriber_exists(message.from_user.id)):
        # Если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id)
    else:
        # Если он уже есть, то просто обновляем ему статус подписки
        db.update_subscriptions(message.from_user.id, True)

    await message.answer("Вы успешно подписались на рассылку!\nЖдите скоро выйдут новые обзоры и вы узнаете о них первыми =)")

# Команда активации отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if(not db.subscriber_exists(message.from_user.id)):
        # Если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы и так не подписанны.")
    else:
        # Если он уже есть то просто обновляем ему статус подписки
        db.update_subscriptions(message.from_user.id, False)
        await message.answer("Вы успешно отписанны от рассылки.")

# Проверяем наличие новых игр и делаем рассылки
async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        # Проверяем наличие новых игр
        new_games = sg.new_games()

        if(new_games):
            # Если игры есть, переворачиваем список и итерируем
            new_games.reverse()
            for ng in new_games:
                # Парсим инфу о новой игре
                nfo = sg.game_info(ng)

                # Получаем список подписчиков бота
                subscriptions = db.get_subscriptions()

                # Отправляем всем новость
                with open(sg.download_image(nfo['image']), 'rb') as photo:
                    for s in subscriptions:
                        await bot.send_photo(
                            s[1],
                            photo,
                            caption = nfo['title'] + "\n" + "Оценка: " + nfo['score'] + "\n" + nfo['excerpt'] + "\n\n" + nfo['link'],
                            disable_notification = True
                        )

                # Обновляем ключ
                sg.update_lastkey(nfo['id'])



# Запускаем лонг поллинг
if __name__ == '__main__':
    dp.loop.create_task(scheduled(10)) # Пока оставим 10 секунд в качестве теста
    executor.start_polling(dp, skip_updates=True)
