from aiogram.fsm.state import State, StatesGroup


class EnterStates(StatesGroup):
    choosing_project = State()
    adding_new = State()
    entering_sum = State()


class ReportStates(StatesGroup):
    choosing_project = State()
    creating_report = State()


class EditModeStates(StatesGroup):
    choosing_project = State()
    choosing_sum = State()
    editing_sum = State()

