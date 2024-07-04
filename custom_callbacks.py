from aiogram.filters.callback_data import CallbackData


class ProjectCallback(CallbackData, prefix='pr'):
    project_id: int
    project_name: str
    action: str


class PageCallback(CallbackData, prefix='pg'):
    direction: str
    action: str
