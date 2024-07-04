from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db_manager import get_projects

from custom_callbacks import ProjectCallback, PageCallback

async def projects_kb(page, total_pages, add_new=False):
    projects = await get_projects(limit=8, offset=page*8)

    kb = InlineKeyboardBuilder()

    for p in projects:
        kb.button(text=p.name, callback_data=ProjectCallback(project_id=p.id, project_name=p.name, action='choose').pack())

    kb.adjust(1)

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(types.InlineKeyboardButton(text='<<', callback_data=PageCallback(direction='prev', action='page').pack()))
        nav_row.append(types.InlineKeyboardButton(text=f'{page+1}/{total_pages}', callback_data='none'))
        if page < total_pages - 1:
            nav_row.append(types.InlineKeyboardButton(text='>>', callback_data=PageCallback(direction='next', action='page').pack()))

        kb.row(*nav_row)

    if add_new:
        kb.row(types.InlineKeyboardButton(text='Новый проект', callback_data=ProjectCallback(project_id=-1, project_name="", action='new').pack()))

    return kb


