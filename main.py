import telebot
from telebot import types
import requests
from deep_translator import GoogleTranslator

from database import Database

# Настройки
TOKEN = "8136756259:AAHOZQjyrUplYf11gntSi5DTpc-G9vNI6fg"
SPOONACULAR_API_KEY = "97bdb917db30460c98e81c109023a009"

bot = telebot.TeleBot(TOKEN)
database = Database()

# Словарь для перевода популярных блюд (:))
RU_TO_EN_DISHES = {
    "паста карбонара": "pasta carbonara",
    "борщ": "borscht",
    "плов": "pilaf",
    "пельмени": "dumplings",
    "оладьи": "pancakes",
    "блины": "blini",
    "лазанья": "lasagne",
    "пицца": "pizza",
    "суши": "sushi",
    "роллы": "rolls",
    "бургер": "burger",
    "картофель фри": "french fries",
    "салат оливье": "olivier salad",
    "селедка под шубой": "herring under a fur coat",
    "винегрет": "vinaigrette salad",
    "шашлык": "shashlik (grilled meat)",
    "курица гриль": "grilled chicken",
    "котлеты": "cutlets",
    "гречка": "buckwheat",
    "макароны по-флотски": "navy-style pasta",
    "суп харчо": "kharcho soup",
    "солянка": "solyanka soup",
    "щи": "shchi (cabbage soup)",
    "рассольник": "rassolnik soup",
    "гуляш": "goulash",
    "бефстроганов": "beef stroganoff",
    "голубцы": "stuffed cabbage rolls",
    "манты": "manti (dumplings)",
    "хинкали": "khinkali (dumplings)",
    "шаурма": "shawarma",
    "кебаб": "kebab",
    "салат цезарь": "caesar salad",
    "греческий салат": "greek salad",
    "салат капрезе": "caprese salad",
    "рис": "rice",
    "картофельное пюре": "mashed potatoes",
    "жареная картошка": "fried potatoes",
    "яичница": "fried eggs",
    "омлет": "omelet",
    "сырники": "syrniki (cheese pancakes)",
    "творожная запеканка": "tvorog (cottage cheese) casserole",
    "манная каша": "semolina porridge",
    "рисовая каша": "rice porridge",
    "гречневая каша": "buckwheat porridge",
    "овсяная каша": "oatmeal",
    "пирожки": "pirozhki (small pies)",
    "пироги": "pirogi (pies)",
    "вареники": "vareniki (dumplings)",
    "блинчики с мясом": "blinchiki with meat",
    "чай": "tea",
    "кофе": "coffee"
}


# Кнопки
def food_search_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Поиск рецептов(рецепты и продукты, но не более 150 запросов в день)"))
    markup.add(types.KeyboardButton("История моих запросов"))
    markup.add(types.KeyboardButton("Нравится☺"))
    return markup


def favorite_markup(recipe_id, recipe_part=0, is_small=True):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❤️ Добавить в избранное", callback_data=f"add_favorite_{recipe_id}"))
    if not is_small:
        if recipe_part == 0:
            markup.add(types.InlineKeyboardButton("Вперед",
                                                  callback_data=f"receipe_part_{recipe_id}_{recipe_part + 1}"))
        elif 0 < recipe_part < 2:
            markup.add(types.InlineKeyboardButton("Вперед",
                                                  callback_data=f"receipe_part_{recipe_id}_{recipe_part + 1}"))
            markup.add(types.InlineKeyboardButton("Назад",
                                                  callback_data=f"receipe_part_{recipe_id}_{recipe_part - 1}"))
        else:
            markup.add(types.InlineKeyboardButton("Назад",
                                                  callback_data=f"receipe_part_{recipe_id}_{recipe_part - 1}"))
    return markup


def translate_text(text, source="en", target="ru"):
    """Универсальная функция перевода текста с использованием deep-translator"""
    try:
        if not text:
            return text

        # Для перевода с русского на английский
        if source == "ru" and target == "en":
            # Сначала проверяем словарь
            lower_text = text.lower()
            if lower_text in RU_TO_EN_DISHES:
                return RU_TO_EN_DISHES[lower_text]

            # Если нет в словаре, используем переводчик
            return GoogleTranslator(source='ru', target='en').translate(text)

        # Для перевода с английского на русский
        elif source == "en" and target == "ru":
            return GoogleTranslator(source='en', target='ru').translate(text)

        return text
    except Exception as e:
        print(f"Translation error: {e}")
        return text


# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🍴 Я помогу найти рецепт! Нажмите кнопку ниже:",
        reply_markup=food_search_markup()
    )
    database.add_user(message.from_user.id, message.from_user.username)


# Обработчик кнопки "Поиск рецептов"
@bot.message_handler(func=lambda message: message.text.startswith("Поиск рецептов"))
def ask_for_dish(message):
    bot.send_message(message.chat.id, "Введите название блюда на русском (например, 'борщ'):")
    bot.register_next_step_handler(message, search_recipe)


# Обработчик кнопки "История моих запросов"
@bot.message_handler(func=lambda message: message.text.startswith("История моих запросов"))
def show_history(message):
    history_records = database.get_user_history(message.chat.id)

    if not history_records:
        bot.send_message(message.chat.id, "Вы еще не искали рецепты.")
        return

    history_text = "📜 Ваша история запросов:\n\n"
    for i, record in enumerate(history_records, 1):
        dish_name, recipe_title, timestamp = record
        history_text += f"{i}. <b>{dish_name}</b>\n   Найдено: {recipe_title}\n   {timestamp}\n\n"

    bot.send_message(message.chat.id, history_text, parse_mode="HTML")


@bot.message_handler(func=lambda message: message.text == "Нравится☺")
def show_favorites(message):
    favorites = database.get_favourites_count(message.from_user.id)

    if favorites == 0:
        bot.send_message(message.chat.id, "У вас пока нет избранных рецептов.")
        return

    current_page = 0
    show_favorites_page(message.chat.id, message.from_user.id, current_page)


def show_favorites_page(chat_id, user_id, page=0):
    favorites = database.get_favourites(user_id)
    total_pages = (len(favorites) + 9) // 10

    start_idx = page * 10
    end_idx = start_idx + 10
    page_favorites = favorites[start_idx:end_idx]

    markup = types.InlineKeyboardMarkup()

    for recipe in page_favorites:
        markup.add(types.InlineKeyboardButton(
            text=recipe[1],
            callback_data=f"recipe_{recipe[0]}"
        ))

    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"fav_prev_{page - 1}"
        ))

    if page < total_pages - 1:
        pagination_buttons.append(types.InlineKeyboardButton(
            text="Вперёд ➡️",
            callback_data=f"fav_next_{page + 1}"
        ))

    if pagination_buttons:
        markup.row(*pagination_buttons)

    bot.send_message(
        chat_id,
        f"❤️ Ваши избранные рецепты: (страница {page + 1}/{total_pages}):",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith(('fav_prev_', 'fav_next_')))
def handle_favorites_pagination(call):
    action, page = call.data.split('_')[1], int(call.data.split('_')[2])
    show_favorites_page(call.message.chat.id, call.from_user.id, page)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('recipe_'))
def handle_recipe_selection(call):
    recipe_id = int(call.data.split('_')[1])
    resp = database.get_recipe(recipe_id)
    show_recipe(call.message, resp[2], resp[3], resp[4], resp[5], resp[6], resp[7], resp[1])


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_favorite_"))
def add_to_favorites(call):
    recipe_id = call.data.split("_")[-1]

    recipe = database.get_favourite(call.from_user.id, recipe_id)

    if recipe is not None:
        bot.answer_callback_query(call.id, "Этот рецепт уже в избранном")
        return

    database.add_favourite(call.from_user.id, recipe_id)

    bot.answer_callback_query(call.id, "Рецепт добавлен в избранное")


@bot.callback_query_handler(func=lambda call: call.data.startswith("receipe_part_"))
def get_next_part(call):
    data = list(call.data.split("_"))

    recipe_id = data[-2]
    part = int(data[-1])

    data = database.get_recipe(recipe_id)
    title_ru = data["title"]
    source_url = data["spoon_url"]

    try:
        if part == 0:
            ingridients = data["ingridients"]
            text = f"""
            <b>{title_ru}</b>

            {ingridients}

            🔗 <a href="{source_url}">Полный рецепт</a>
            """
            markup = favorite_markup(recipe_id, 0, False)
        elif part == 1:
            instructions = data["instructions"]
            text = f"""
            <b>{title_ru}</b>

            {instructions}

            🔗 <a href="{source_url}">Полный рецепт</a>
            """
            markup = favorite_markup(recipe_id, 1, False)
        elif part == 2:
            nutritional = data["nutritional"]
            text = f"""
            <b>{title_ru}</b>

            {nutritional}

            🔗 <a href="{source_url}">Полный рецепт</a>
            """
            markup = favorite_markup(recipe_id, 2, False)

        # Проверяем длину текста перед отправкой
        if len(text) > 1024:
            text = text[:1000] + "...\n\n🔗 <a href=\"{source_url}\">Полный рецепт</a>"

        bot.edit_message_caption(
            caption=text,
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Error in get_next_part: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при обработке запроса")


# Поиск рецепта
def search_recipe(message):
    dish_ru = message.text.strip().lower()

    # Переводим на английский для поиска
    dish_en = translate_text(dish_ru, "ru", "en")

    bot.send_message(message.chat.id, f"🔍 Ищем: {dish_ru}...")

    try:
        # Ищем в Spoonacular
        if dish_ru in RU_TO_EN_DISHES:
            search_url = f"https://api.spoonacular.com/recipes/complexSearch?query={dish_en}&apiKey={SPOONACULAR_API_KEY}"
            response = requests.get(search_url, timeout=15)
        else:
            search_url = f"https://api.spoonacular.com/recipes/complexSearch?query={dish_ru}&apiKey={SPOONACULAR_API_KEY}"
            response = requests.get(search_url, timeout=15)
        data = response.json()

        if not data.get("results"):
            bot.send_message(message.chat.id, "😢 Рецепт не найден. Попробуйте другое название.")
            return

        # Получаем детали первого найденного рецепта
        recipe_id = data["results"][0]["id"]
        recipe_info = get_recipe_info(recipe_id)

        if not recipe_info:
            bot.send_message(message.chat.id, "😢 Не удалось получить информацию о рецепте.")
            return

        # Сохраняем в историю
        recipe_title = recipe_info.get("title", "Без названия")
        database.add_history(message.chat.id, dish_ru, recipe_title)

        image = recipe_info.get("image")

        # Формируем и отправляем результат на русском
        ingridients, instructions, calories, title_ru, source_url = format_recipe_info(recipe_info)

        database.add_receipt(recipe_id, image, title_ru, ingridients, instructions, calories, source_url)
        show_recipe(message, image, title_ru, ingridients, instructions, calories, source_url, recipe_id)

    except requests.exceptions.Timeout:
        bot.send_message(message.chat.id, "⏳ Время поиска истекло. Попробуйте позже.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка: {str(e)}")


def show_recipe(message, image, title_ru, ingridients, instructions, calories, source_url, recipe_id):
    try:
        text = f"""
        <b>{title_ru}</b>

        {ingridients}

        {instructions}

        {calories}

        🔗 <a href="{source_url}">Полный рецепт</a>
        """

        is_small = len(text) < 1024

        if is_small:
            markup = favorite_markup(recipe_id)
        else:
            text = f"""
                <b>{title_ru}</b>

                {ingridients}

                🔗 <a href="{source_url}">Полный рецепт</a>
                """
            markup = favorite_markup(recipe_id, 0, False)

        if image is None:
            bot.send_message(message.chat.id, text,
                             parse_mode="HTML",
                             reply_markup=markup)
        else:
            # Убедимся, что текст не слишком длинный
            if len(text) > 1024:
                text = text[:1000] + "...\n\n🔗 <a href=\"{source_url}\">Полный рецепт</a>"

            bot.send_photo(message.chat.id,
                           image,
                           parse_mode="HTML",
                           reply_markup=markup,
                           caption=text)
    except Exception as e:
        print(f"Error in show_recipe: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отображении рецепта")


def get_recipe_info(recipe_id):
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={SPOONACULAR_API_KEY}&includeNutrition=true"
        response = requests.get(url, timeout=15)
        return response.json()
    except Exception as e:
        print(f"Error getting recipe info: {e}")
        return None


def format_recipe_info(recipe_data):
    """Форматируем информацию о рецепте на русском языке"""
    # Переводим название
    title = recipe_data.get("title", "Без названия")
    title_ru = translate_text(title, "en", "ru")

    # Получаем питательную ценность
    nutrition = recipe_data.get("nutrition", {})
    nutrients = nutrition.get("nutrients", [])

    calories = next((n for n in nutrients if n.get("name") == "Calories"), {}).get("amount", "?")
    protein = next((n for n in nutrients if n.get("name") == "Protein"), {}).get("amount", "?")

    # Получаем инструкции
    instructions = ""
    if recipe_data.get("analyzedInstructions") and len(recipe_data["analyzedInstructions"]) > 0:
        # Собираем пошаговые инструкции
        steps = recipe_data["analyzedInstructions"][0].get("steps", [])
        for step in steps:
            translated_step = translate_text(step['step'], "en", "ru")
            instructions += f"{step['number']}. {translated_step}\n"
    else:
        # Используем обычные инструкции, если нет пошаговых
        instructions = translate_text(recipe_data.get("instructions", "Инструкции отсутствуют."), "en", "ru")

    # Переводим список ингредиентов
    extended_ingredients = recipe_data.get("extendedIngredients", [])
    ingredients_ru = []
    for ing in extended_ingredients:
        original_text = ing.get('original', '?')
        translated_ingredient = translate_text(original_text, "en", "ru")
        ingredients_ru.append(f"• {translated_ingredient}")

    ingredients_ru_text = "\n".join(ingredients_ru) if ingredients_ru else "Ингредиенты не указаны."

    # Получаем ссылку на рецепт
    source_url = recipe_data.get("sourceUrl", "#")

    # Формируем окончательное сообщение
    return beautify_recipe(title_ru, ingredients_ru_text, instructions, calories, protein, source_url)


def beautify_recipe(title_ru, ingredients_ru_text, instructions, calories, protein, source_url):
    ingridients = f"""
        📝 <b>Ингредиенты:</b>
        {ingredients_ru_text}
    """

    instructions = f"""
        📋 <b>Инструкции:</b>
        {instructions}
    """

    calories = f"""
        ⚖️ <b>Пищевая ценность:</b>
        🔥 Калории: {calories} ккал
        🥩 Белки: {protein} г
    """

    return ingridients, instructions, calories, title_ru, source_url


if __name__ == "__main__":
    print("Бот запущен")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка в работе бота: {e}")