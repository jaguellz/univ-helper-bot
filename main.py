import telebot
import requests
import schedule
import json
import time
with open('.env') as env:
    f = env.readlines()
    f = list(map(lambda x: x.split('"'), f))
    token = f[0][1]
    chat_id = f[1][1]


lesson_checker = "Был сегодня на парах?"
lesson_notification = 'Привет! Пары через час, не опаздывай)'
bot = telebot.TeleBot(token)


def makePostButtons(data=None):
    if not data:
        data = (0, 0)
    buttons = [
        [{"text": f"Был - {data[0]}", "callback_data": "yes"}],
        [{"text": f"Не был - {data[1]}", "callback_data": "no"}],
    ]
    keyboard = {'inline_keyboard': buttons}
    keyboard = json.dumps(keyboard)
    return keyboard


def postWButtons(text):
    markup = {'chat_id': chat_id, 'text': text, 'reply_markup': makePostButtons()}
    sendPost(markup)


def sendPost(keys):
    r = requests.get(
        'https://api.telegram.org/'
        'bot' + token + '/sendMessage',
        params=keys
    )


@bot.callback_query_handler(func=lambda call: True)
def reactionCallback(call):
    ans = call.data
    callback_id = call.id
    post_time = call.message.date
    person = call.from_user.username
    data = [int(call.message.reply_markup.keyboard[0][0].text.split(' - ')[1]),
            int(call.message.reply_markup.keyboard[1][0].text.split(' - ')[1])]
    with open('log.csv', 'r') as file:
        content = file.readlines()
    content = list(map(lambda x: x.split('\n')[0].split(';'), content))
    if not (time.strftime("%d.%m.%Y", time.localtime(post_time)) in content[0]):
        content[0].append(time.strftime("%d.%m.%Y", time.localtime(post_time)))
        list(map(lambda x: x.append('0'), content[1::]))
    index = content[0].index(time.strftime("%d.%m.%Y", time.localtime(post_time)))
    for i in content:
        if person == i[1]:
            if ans == 'yes' and i[index] == '0':
                data[0] += 1
                i[index] = '+'
            elif ans == 'no' and i[index] == '0':
                data[1] += 1
                i[index] = '-'
            elif ans == 'no' and i[index] == '+':
                data[1] += 1
                data[0] -= 1
                i[index] = '-'
            elif ans == 'yes' and i[index] == '-':
                data[0] += 1
                data[1] -= 1
                i[index] = '+'
            else:
                requests.get(
                    'https://api.telegram.org/'
                    'bot' + token + '/answerCallbackQuery',
                    params={'callback_query_id': callback_id, 'text': 'Вы уже отметились', 'show_alert': True}
                )
            break
    keyboard = makePostButtons(data)
    keys = {'chat_id': chat_id, 'message_id': call.message.message_id, 'reply_markup': keyboard}
    r = requests.get(
        'https://api.telegram.org/'
        'bot' + token + '/editMessageReplyMarkup',
        params=keys
    )
    with open('log.csv', 'w') as file:
        content = list(map(lambda x: ';'.join(x) + '\n', content))
        file.writelines(content)


def scheduler():
    schedule.every().monday.at('14:30').do(sendPost, {'chat_id': chat_id, 'text': lesson_notification})
    schedule.every().tuesday.at('14:30').do(sendPost, {'chat_id': chat_id, 'text': lesson_notification})
    schedule.every().wednesday.at('10:40').do(sendPost, {'chat_id': chat_id, 'text': lesson_notification})
    schedule.every().thursday.at('14:30').do(sendPost, {'chat_id': chat_id, 'text': lesson_notification})
    schedule.every().friday.at('14:30').do(sendPost, {'chat_id': chat_id, 'text': lesson_notification})

    schedule.every().monday.at('20:00').do(postWButtons, lesson_checker)
    schedule.every().tuesday.at('20:00').do(postWButtons, lesson_checker)
    schedule.every().wednesday.at('20:00').do(postWButtons, lesson_checker)
    schedule.every().thursday.at('20:00').do(postWButtons, lesson_checker)
    schedule.every().friday.at('20:00').do(postWButtons, lesson_checker)


scheduler()
while True:
    bot.infinity_polling()
    schedule.run_pending()
