from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db_manager import get_projects, get_sums_with_dates

from custom_callbacks import ProjectCallback, PageCallback, SumCallback


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


async def sums_selector_kb(project_id, page, total_pages):
    sums = await get_sums_with_dates(project_id, limit=10, offset=page*10)

    kb = InlineKeyboardBuilder()

    for s in sums:
        row = []
        row.append(types.InlineKeyboardButton(text=f'{s[1].strftime("%d.%m.%Y %H:%M")}', callback_data='none'))
        row.append(types.InlineKeyboardButton(text=f'{s[2]}', callback_data=SumCallback(sum_db_id=s[0], sum_value=s[2], action='sum_select').pack()))
        kb.row(*row)

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(types.InlineKeyboardButton(text='<<', callback_data=PageCallback(direction='prev', action='page').pack()))
        nav_row.append(types.InlineKeyboardButton(text=f'{page+1}/{total_pages}', callback_data='none'))
        if page < total_pages - 1:
            nav_row.append(types.InlineKeyboardButton(text='>>', callback_data=PageCallback(direction='next', action='page').pack()))

        kb.row(*nav_row)

    return kb


