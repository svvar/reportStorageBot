import math
import configparser
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import F, Router
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext
from states import EnterStates, ReportStates, EditModeStates

from db_manager import *
from excel_writer import write_excel_to_buffer
from custom_callbacks import ProjectCallback, PageCallback, SumCallback
from keyboard_helper import projects_kb, sums_selector_kb


dp = Dispatcher()
router = Router()

'''
Entering sum/adding project section
'''


@dp.message(Command('start'))
async def start(message: types.Message):
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text='Ввести сумму по проекту')
    keyboard.button(text='Выгрузить отчёт по проекту')
    keyboard.button(text='Изменить данные по проекту')
    keyboard.adjust(1)

    await message.answer('Hello!', reply_markup=keyboard.as_markup())


@router.message(F.text.lower() == 'ввести сумму по проекту')
async def add_sum_project_menu(message: types.Message, state: FSMContext):
    total = await get_projects_count()
    page = 0
    pages = math.ceil(total / 8)
    await state.update_data(page=page)

    kb = await projects_kb(page, pages, add_new=True)

    await message.answer('Выберите проект', reply_markup=kb.as_markup())
    await state.set_state(EnterStates.choosing_project)


@router.callback_query(PageCallback.filter(F.action == 'page'), EnterStates.choosing_project)
async def change_page(query: types.CallbackQuery, callback_data: PageCallback, state: FSMContext):
    page = (await state.get_data())['page']
    if callback_data.direction == 'next':
        page += 1
    else:
        page -= 1

    await state.update_data(page=page)

    total = await get_projects_count()
    pages = math.ceil(total / 8)
    kb = await projects_kb(page, pages, add_new=True)


    await query.message.edit_reply_markup(reply_markup=kb.as_markup())
    await query.answer()


@router.callback_query(ProjectCallback.filter(F.action == 'choose'), EnterStates.choosing_project)
async def project_chosen_entering_sum(query: types.CallbackQuery, callback_data: ProjectCallback, state: FSMContext):
    project_id = callback_data.project_id

    await query.message.answer('Введите сумму')
    await state.set_state(EnterStates.entering_sum)
    await state.update_data(project_id=project_id)
    await query.answer()


@router.callback_query(ProjectCallback.filter(F.action == 'new'), EnterStates.choosing_project)
async def new_project(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Введите название нового проекта')
    await state.set_state(EnterStates.adding_new)
    await query.answer()


@router.message(EnterStates.adding_new)
async def new_project_entered(message: types.Message, state: FSMContext):
    project_name = message.text
    await add_project(project_name)
    await message.answer('Проект добавлен успешно!')
    await state.clear()


@router.message(EnterStates.entering_sum)
async def sum_entered(message: types.Message, state: FSMContext):
    try:
        sum = float(message.text.replace(',', '.'))
        await save_sum((await state.get_data())['project_id'], sum)
        await message.answer('Сумма введена успешно!')
        await state.clear()
    except ValueError:
        await message.answer('Сумма должна быть числом! Повторите ввод')
        return


'''
Report generation section
'''


@router.message(F.text.lower() == 'выгрузить отчёт по проекту')
async def report_project_menu(message: types.Message, state: FSMContext):
    total = await get_projects_count()
    page = 0
    pages = math.ceil(total / 8)
    await state.update_data(page=page)

    kb = await projects_kb(page, pages)

    await message.answer('Выберите проект', reply_markup=kb.as_markup())
    await state.set_state(ReportStates.choosing_project)


@router.callback_query(PageCallback.filter(F.action == 'page'), EditModeStates.choosing_project)
@router.callback_query(PageCallback.filter(F.action == 'page'), ReportStates.choosing_project)
async def change_projects_page(query: types.CallbackQuery, callback_data: PageCallback, state: FSMContext):
    page = (await state.get_data())['page']
    if callback_data.direction == 'next':
        page += 1
    else:
        page -= 1

    await state.update_data(page=page)

    total = await get_projects_count()
    pages = math.ceil(total / 8)
    kb = await projects_kb(page, pages)

    await query.message.edit_reply_markup(reply_markup=kb.as_markup())
    await query.answer()


@router.callback_query(ProjectCallback.filter(F.action == 'choose'), ReportStates.choosing_project)
async def generate_report(query: types.CallbackQuery, callback_data: ProjectCallback, state: FSMContext):
    project_id = callback_data.project_id

    last_report_date = await get_last_report_date(project_id)
    if last_report_date:
        await query.message.answer(f'Отчёт по проекту {callback_data.project_name} с {last_report_date.strftime("%d.%m.%y %H:%M")}')
        sums = await get_sums_by_date(project_id, last_report_date)
    else:
        await query.message.answer(f'Это первый отчёт по проекту {callback_data.project_name}')
        sums = await get_sums_by_date(project_id)

    await update_report_date(project_id)

    filename = (f'Отчёт {callback_data.project_name} '
                f'{last_report_date.strftime("%d.%m.%y %H.%M") if last_report_date is not None else ""}'
                f' - {datetime.datetime.now().strftime("%d.%m.%y %H.%M")}.xlsx')
    with BytesIO() as file:
        await write_excel_to_buffer(sums, file)
        input_file = BufferedInputFile(file.getvalue(), filename=filename)
        await query.message.answer_document(document=input_file)

    await query.answer()
    await state.clear()


'''
Changing project data section
'''

@router.message(F.text.lower() == 'изменить данные по проекту')
async def change_project_menu(message: types.Message, state: FSMContext):
    total = await get_projects_count()
    page = 0
    pages = math.ceil(total / 8)
    await state.update_data(page=page)

    kb = await projects_kb(page, pages)

    await message.answer('Выберите проект', reply_markup=kb.as_markup())
    await state.set_state(EditModeStates.choosing_project)

@router.callback_query(ProjectCallback.filter(F.action == 'choose'), EditModeStates.choosing_project)
async def project_chosen_edit(query: types.CallbackQuery, callback_data: ProjectCallback, state: FSMContext):
    project_id = callback_data.project_id
    last_report_date = await get_last_report_date(project_id)
    no_report_yet = False
    if last_report_date is None:
        last_report_date = datetime.datetime(2020, 1, 1, 0, 0, 0)
        no_report_yet = True
    sums_count = await get_sums_count_by_project(project_id, last_report_date)

    last_date_string = 'с ' + last_report_date.strftime("%d.%m.%y %H:%M") if not no_report_yet else ""

    if sums_count == 0:
        await query.message.answer(f'Нет данных для изменения {last_date_string}')
        await query.answer()
        return

    page = 0
    pages = math.ceil(sums_count / 10)
    await state.update_data(project_id=project_id, sums_count=sums_count, sum_page=page, sum_pages=pages, last_rep_date=last_report_date)
    kb = await sums_selector_kb(project_id, last_report_date, page, pages)

    await query.message.answer(
        f'Выберите запись для изменения {last_date_string} в правой колонке',
        reply_markup=kb.as_markup())
    await state.set_state(EditModeStates.choosing_sum)
    await query.answer()


@router.callback_query(PageCallback.filter(F.action == 'page'), EditModeStates.choosing_sum)
async def change_page_edit(query: types.CallbackQuery, callback_data: PageCallback, state: FSMContext):
    data = await state.get_data()
    page = data['sum_page']
    pages = data['sum_pages']
    project = data['project_id']
    last_report_date = data['last_rep_date']
    if callback_data.direction == 'next':
        page += 1
    else:
        page -= 1

    await state.update_data(sum_page=page)
    kb = await sums_selector_kb(project, last_report_date, page, pages)

    await query.message.edit_reply_markup(reply_markup=kb.as_markup())
    await query.answer()


@router.callback_query(SumCallback.filter(F.action == 'sum_select'), EditModeStates.choosing_sum)
async def sum_chosen_edit(query: types.CallbackQuery, callback_data: SumCallback, state: FSMContext):
    sum_id = callback_data.sum_db_id
    sum = callback_data.sum_value
    await state.update_data(sum_id=sum_id)

    await state.set_state(EditModeStates.editing_sum)
    await query.message.answer(f'Введите новую сумму вместо {sum}')
    await query.answer()


@router.message(EditModeStates.editing_sum)
async def sum_entered_edit(message: types.Message, state: FSMContext):
    try:
        sum = float(message.text.replace(',', '.'))
        await update_sum((await state.get_data())['sum_id'], sum)
        await message.answer('Сумма изменена успешно!')
        await state.clear()
    except ValueError:
        await message.answer('Сумма должна быть числом! Повторите ввод')
        return


async def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    token = config['tg']['bot_api_token']

    bot = Bot(token=token)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())