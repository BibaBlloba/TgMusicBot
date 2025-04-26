import asyncio
import os
from random import randint
import tempfile
import yt_dlp
from config import settings
from aiogram import types, F
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

bot = settings.bot
dp = settings.dp


async def download_media(url: str, is_video: bool) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
            if is_video
            else 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'restrictfilenames': True,
        }

        if not is_video:
            ydl_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            actual_filename = ydl.prepare_filename(info)

            if not os.path.exists(actual_filename):
                base_name = os.path.splitext(actual_filename)[0]
                for ext in ['.webm', '.mp4', '.m4a', '.mp3']:
                    if os.path.exists(base_name + ext):
                        actual_filename = base_name + ext
                        break
                else:
                    raise FileNotFoundError(f'Не удалось найти файл: {actual_filename}')

            with open(actual_filename, 'rb') as f:
                file_data = f.read()

            return {
                'data': file_data,
                'title': info.get('title', 'media').replace('/', '_')[:50],
                'duration': info.get('duration', 0),
            }


class DownloadStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_choice = State()


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer('Xui')


@dp.message(F.text.regexp(r'(https?://)?(www\.)?(youtube|youtu)\.(com|be)/.+'))
async def handle_youtube_url(message: types.Message, state: FSMContext):
    await state.set_state(DownloadStates.waiting_for_choice)
    await state.update_data(url=message.text)

    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text='Видосик', callback_data='video'),
        types.InlineKeyboardButton(text='M4A', callback_data='audio'),
    )

    await message.answer('a?', reply_markup=builder.as_markup())


@dp.callback_query(DownloadStates.waiting_for_choice, F.data.in_(['video', 'audio']))
async def process_link(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    url = data['url']
    is_video = callback.data == 'video'

    await callback.message.edit_text('щас')
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id

    try:
        result = await download_media(url, is_video)
        file_ext = '.mp4' if is_video else '.mp3'
        file = types.BufferedInputFile(
            result['data'], filename=f'{result["title"]}{file_ext}'
        )

        if is_video:
            await callback.message.answer_video(file, duration=result['duration'])
        else:
            await callback.message.answer_audio(file, duration=result['duration'])
    except yt_dlp.DownloadError:
        await callback.message.answer('Плейлисты не качаю')
    except Exception:
        await callback.message.answer('Ошибка: Все по пизде')
    finally:
        await callback.bot.delete_message(chat_id=chat_id, message_id=message_id)
        await state.clear()


@dp.message()
async def unknown_message(message: types.Message):
    random_choise = randint(0, 2)
    match random_choise:
        case 0:
            await message.answer('Чо?')
        case 1:
            await message.answer('Нипон')
        case 2:
            await message.answer('А?')


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
