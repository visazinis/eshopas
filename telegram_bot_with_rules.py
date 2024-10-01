
import pandas as pd
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

# Логирование для отслеживания ошибок и работы бота
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные для поддержки и настроек
support_phone = "+37063888895"
support_email = "nikita@hotmail.lt"
api_key = 'AIzaSyBoymkLEtddTo7nTHGw9x4XGAQQpAACBPw'
cse_id = '321b5ef52c29e44d3'

# Правила и политика на литовском языке
rules_text = '''
Pirkimo, grąžinimo ir garantijos taisyklės pagal Europos Sąjungos reglamentus:

1. **Informacija prieš pirkimą**
- Pardavėjas privalo pateikti pirkėjui visą informaciją apie prekę prieš pirkimą, įskaitant kainą, sąlygas ir kt.

2. **Grąžinimo teisė per 14 dienų**
- Pirkėjas turi teisę grąžinti prekę per 14 dienų be paaiškinimo. Prekė turi būti grąžinta originalioje būklėje.

3. **Garantijos įsipareigojimai**
- Visoms prekėms suteikiama 2 metų garantija, pradedant nuo pirkimo dienos.

4. **Asmens duomenų apsaugos taisyklės (GDPR)**
- Pirkėjų asmens duomenys tvarkomi laikantis GDPR reglamento ir naudojami tik užsakymo vykdymui.

Jei turite klausimų, kreipkitės į mus telefonu {support_phone} arba el. paštu {support_email}.
'''

# Загрузка данных из Excel-файла
def load_data():
    try:
        data = pd.read_excel('Prekes_20240930032912.xlsx')
        return data
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        return None

# Функция поиска изображений через Google API
def google_image_search(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image&key={api_key}&cx={cse_id}"
        response = requests.get(url).json()
        image_links = [item['link'] for item in response.get('items', [])[:2]]
        return image_links if image_links else []
    except Exception as e:
        logger.error(f"Ошибка поиска изображений: {e}")
        return []

# Команда /rules для отправки правил и политики
def send_rules(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(rules_text.format(support_phone=support_phone, support_email=support_email))

# Корзина покупок для пользователя
def get_cart(context):
    return context.user_data.setdefault('cart', [])

def add_to_cart(context, product):
    cart = get_cart(context)
    cart.append(product)
    context.user_data['cart'] = cart

def clear_cart(context):
    context.user_data['cart'] = []

def remove_from_cart(context, product_name):
    cart = get_cart(context)
    context.user_data['cart'] = [item for item in cart if item['Prekės pavadinimas'] != product_name]

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    data = load_data()
    if data is not None:
        kategorijos = data['Kategorijos'].unique().tolist()
        keyboard = [kategorijos[i:i + 2] for i in range(0, len(kategorijos), 2)]
        update.message.reply_text(
            'Sveiki! Pasirinkite kategoriją:',
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
    else:
        update.message.reply_text('Nepavyko įkelti duomenų apie prekes. Bandykite dar kartą vėliau.')

# Просмотр корзины
def view_cart(update: Update, context: CallbackContext) -> None:
    cart = get_cart(context)
    if cart:
        message = "Jūsų krepšelis:

"
        total_price = 0
        for item in cart:
            message += f"Prekė: {item['Prekės pavadinimas']}, Kaina: {item['Kaina']} EUR
"
            total_price += item['Kaina']
        message += f"
Iš viso: {total_price} EUR"
        update.message.reply_text(message)
    else:
        update.message.reply_text("Jūsų krepšelis yra tuščias.")

# Добавление товара в корзину
def add_to_cart_handler(update: Update, context: CallbackContext) -> None:
    data = load_data()
    if data is not None:
        product_name = update.message.text
        product = data[data['Prekės pavadinimas'].str.contains(product_name, case=False)]
        
        if not product.empty:
            product_row = product.iloc[0].to_dict()
            add_to_cart(context, product_row)

            # Попробуем найти изображение для товара
            image_links = google_image_search(product_row['Prekės pavadinimas'])

            # Если изображение найдено, отправим его с информацией о товаре
            if image_links:
                update.message.reply_photo(photo=image_links[0], caption=f"Prekė: {product_row['Prekės pavadinimas']}
Kaina: {product_row['Kaina']} EUR")
            else:
                # Если изображение не найдено, отправим только текстовую информацию
                update.message.reply_text(f"Prekė: {product_row['Prekės pavadinimas']}
Kaina: {product_row['Kaina']} EUR
(Be paveikslėlio)")
        else:
            update.message.reply_text("Tokios prekės nerasta.")
    else:
        update.message.reply_text("Nepavyko įkelti duomenų apie prekes.")

# Удаление товара из корзины
def remove_from_cart_handler(update: Update, context: CallbackContext) -> None:
    product_name = update.message.text
    remove_from_cart(context, product_name)
    update.message.reply_text(f"Prekė {product_name} pašalinta iš krepšelio.")

# Очистка корзины
def clear_cart_handler(update: Update, context: CallbackContext) -> None:
    clear_cart(context)
    update.message.reply_text("Krepšelis išvalytas.")

# Основная функция запуска бота
def main():
    updater = Updater("7809404826:AAEX1MhnnlN7B6A31CtdQl2572JKNNOUhcQ", use_context=True)
    logger.info("Bot started")
    
    dispatcher = updater.dispatcher

    # Команды и обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("rules", send_rules))  # Команда для отправки правил
    dispatcher.add_handler(CommandHandler("cart", view_cart))  # Команда для просмотра корзины
    dispatcher.add_handler(CommandHandler("clear_cart", clear_cart_handler))  # Команда для очистки корзины
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^remove '), remove_from_cart_handler))  # Удаление товара
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, add_to_cart_handler))  # Добавление товара

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
