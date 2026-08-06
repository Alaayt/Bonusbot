from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    choosing_language = State()
    choosing_country = State()
    typing_country_name = State()
    confirming_age = State()


class MissingBonusFlow(StatesGroup):
    asking_offer_name = State()
    asking_country_currency = State()
    asking_participate_button = State()
    asking_selected_before_deposit = State()
    asking_promo_entered = State()
    asking_deposit_time_amount = State()


class FreeChat(StatesGroup):
    active = State()
