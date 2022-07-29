#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

# Импортируем нужные библиотеки
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from threading import Timer

# Токен бота
TOKEN = ''

# Подключаемся к боту по токену
bot = telegram.Bot(token=TOKEN)

# Подключаемся к updater и dispatcher по токену (видимо, чтобы отслеживать полученные сообщения и отправлять ответы)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Константы
# Статусы пользователей
GUEST = 'GUEST'
ADMIN = 'ADMIN'
COMMAND = 'COMMAND'
# Пароль для входа в админку
ADMIN_PASSWORD = '23032000'
# Ссылка на администратора
ADMIN_LINK = "https://t.me/ar_gilmutdinova"
# Текущее состояние игры
REGISTRATION = 'REGISTRATION'
GAME = 'GAME'
IN_QUESTION = 'IN_QUESTION'
global state
state = REGISTRATION

# Ссылка на турнирную таблицу
global table_URL
table_URL = 'https://docs.google.com/spreadsheets/d/1qTH1Z2K6FIKiN1f8xY_npGG1oo44wKbPGFNyja6H4pU/edit#gid=0'

# Номер текщего вопроса
global current_question
current_question = 0

# Статус пользователя по его id
users_statuses = {}

# Вопрос по его номеру
questions = {}

# Название команды по её номеру
command_names = {}

# Номер команды по id чата, из которого она зарегистрировалась
command_numbers = {}


# Функция регистрации команды. Вызывается, когда приходит сообщение /reg command_name
def command_registration(update, context):
    # Записываем id чата, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Если этот id ещё не зарегистрирован
    if chat_id not in command_numbers.keys():
        # Проверяем, написал ли пользователь название команды после /reg
        if len(context.args) > 0:
            # Если написал, соединяем название команды (например /reg Моя команда имеет два аргумента, которые надо соединить)
            command_name = ' '.join(context.args)
            # Если это первая зареганая команда - присваиваем ей номер 1. Иначе присваеваем ей максимальный номер + 1
            if len(command_names) == 0:
                command_number = 1
            else:
                command_number = max(command_names.keys()) + 1

            # Записываем название команды по её номеру в command_names
            command_names[command_number] = command_name
            # Записываем номер команды по id чата, из которой её зарегистрировали
            command_numbers[chat_id] = command_number
            # Если пользователь не имеет статус ADMIN, присваиваем ему статус COMMAND
            if not check_admin(chat_id):
                # Присваиваем пользователю статус COMMAND
                users_statuses[chat_id] = COMMAND
                # Отправляем ответное сообщение зарегистровавшемуся пользователю
                context.bot.send_message(chat_id=chat_id,
                                         text="Ваша команда успешно зарегистрирована под номером " + str(
                                             command_number) + "\nОжидайте начала игры")
                # Отправляем всем админам сообщение о том, что команда зарегистрировалась
                send_to_all_admins(context,
                                   "Команда " + command_name + " зарегистрировалась под номером " + str(command_number))
        else:
            # Если пользователь не ввёл название команды, сообщаем ему об этом
            context.bot.send_message(chat_id=chat_id,
                                     text="Введите название команды через пробел после /reg\nНапример: /reg Название моей команды")
    else:
        # Если этот пользователь уже зарегистрировал команду
        command_number = command_numbers[chat_id]
        # if нужен на всякий случай, чтобы бот не сломался (если номер команды есть в базе, а названия по этому номеру нет)
        if command_number in command_names.keys():
            command_name = command_names[command_number]
            context.bot.send_message(chat_id=chat_id,
                                     text="Вы уже зарегистрированы под номером " + str(
                                         command_number) + " с названием " + command_name)


# Функция входа в админку (получения статуса ADMIN). Вызов /admin password
def enter_admin_mode(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Если пользователь уже админ, сообщаем ему об этом
    if check_admin(chat_id):
        context.bot.send_message(chat_id=chat_id, text="Вы уже администратор!")
    else:
        # Проверяем, ввёл ли пользователь пароль в аргументах
        if len(context.args) > 0:
            # Проверяем, совпадает ли введённый пароль с константой ADMIN_PASSWORD
            if context.args[0] == ADMIN_PASSWORD:
                # Если совпадает, присваиваем пользователю статус ADMIN
                users_statuses[update.effective_chat.id] = ADMIN
                context.bot.send_message(chat_id=chat_id, text="Вы теперь администратор")
            else:
                # Если не совпадает, сообщаем пользователю об этом
                context.bot.send_message(chat_id=chat_id, text="Неверный пароль!")
        else:
            # Если в аргументах ничего не введено, сообщаем пользователю об этом
            context.bot.send_message(chat_id=chat_id, text="Введите пароль в аргументах!")


# Функция вывода всех зарегистрированных команд. Только для админов. Вызов /getc
def get_commands(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является пользователь с данным id администратором
    if check_admin(chat_id):
        # Если пользователь является администратором - формируем список команд и высылаем ему.
        commands_list = ''
        for command_number in range(1, len(command_names) + 1):
            if command_number in command_names.keys():
                commands_list += '\n' + str(command_number) + '. ' + command_names[command_number]
        context.bot.send_message(chat_id=chat_id,
                                 text="Список зарегистрированных команд:" + commands_list)
    else:
        # Пользователь не является администратором. Сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id,
                                 text="Вы не обладаете правами администратора!")


# Функция, срабатывающая при получении любого сообщения, которое не является командой (не начинается с символа "/" )
def get_message(update, context):
    # Получаем доступ к глобальной переменной состояния
    global state
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем зарегистрирован ли пользователь от которого пришло сообщения (его id есть в command_numbers.keys())
    if chat_id in command_numbers.keys():
        # Если пользователь зарегистрирован, проверяем состояние игры.
        if state == IN_QUESTION:
            # Если игра находится в состоянии IN_QUESTION - отправляем всем администраторам сообщение, которое прислал пользователь
            # При этом к сообщению добавляется номер текущего вопроса и название команды пользователя
            command_number = command_numbers[chat_id]
            command_name = command_names[command_number]
            answer = str(current_question) + '. ' + command_name
            answer += '\n' + update.message.text
            send_to_all_admins(context, answer)
        else:
            # Во всех остальных состояниях игры отправляем следующие сообщения
            if state == GAME:
                context.bot.send_message(chat_id=chat_id, text="Ожидайте следующего вопроса")
            else:
                context.bot.send_message(chat_id=chat_id, text="Ожидайте начала игры")
    else:
        # Если пользователь не зарегистрирован, сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id,
                                 text='Вы не зарегистрированы!\nЗарегистрироваться можно с помощью команды /reg')


# Функция добавения вопроса. Только для админов. Вызов /addq 1 Text of the question
def add_question(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id

    # Проверяем, является ли пользователь администратором
    if check_admin(chat_id):
        # Проверяем, ввёл ли пользователь номер и текст вопроса
        if len(context.args) >= 2:
            if context.args[0].isdigit:
                # Соединяем текст вопроса, добавляем его в список вопросов под номером, который ввёл пользователь
                questions[int(context.args[0])] = context.args[0] + '. ' + ' '.join(
                    context.args[1:(len(context.args) + 1)])
                context.bot.send_message(chat_id=chat_id,
                                         text="Вопрос " + context.args[0] + " добавлен!")
            else:
                # Если первый аргумент команды не является числом
                context.bot.send_message(chat_id=chat_id,
                                         text="Первым аргументом должен быть номер вопроса, вторым - текст вопроса")
        else:
            # Если текст или номер вопроса не введены
            context.bot.send_message(chat_id=chat_id,
                                     text="Первым аргументом должен быть номер вопроса, вторым - текст вопроса")
    else:
        # Если пользователь не является администратором
        context.bot.send_message(chat_id=chat_id,
                                 text="Вы не обладаете правами администратора!")


# Функция удаления всех вопросов. Только для админов. Вызов /clearq
def clear_questions(update, context):
    chat_id = update.effective_chat.id
    if check_admin(chat_id):
        questions.clear()
        context.bot.send_message(chat_id=chat_id, text="Все вопросы удалены!")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Вы не обладаете правами администратора!")


# Функция вывода всех вопросов. Только для админов. Вызов /getq
def get_questions(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        # Если пользователь является админом, проверяем, есть ли сохранённые вопросы
        if len(questions) > 0:
            # Если список вопросов не пуст, выводим все вопросы от 0го по максимальный, который добавлен на данный момент
            # Если, например, уже добавлен 5й вопрос, но ещё не добавлены 4й и 3й, вместо их текста выведется прочерк.
            for i in range(0, max(questions.keys()) + 1):
                if i in questions.keys():
                    context.bot.send_message(chat_id=chat_id, text=questions[i])
                else:
                    context.bot.send_message(chat_id=chat_id, text=str(i) + ". -")
        else:
            # Если список вопросов пуст, сообщаем об этом пользователю
            context.bot.send_message(chat_id=chat_id, text="Список вопросов пуст!")
    else:
        # Если пользователь не является админом, сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id,
                                 text="Вы не обладаете правами администратора!")


# Функция начала игры. Доступна только админам. Вызов /start_game
def start_game(update, context):
    # Получаем глобальную переменную текущего вопроса
    global current_question
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        # Меняем состояние игры на GAME, устанавливаем номер текущего вопроса на 0
        set_state(GAME)
        current_question = 0
        # Отправляем сообщение о начале игры всем администраторам и всем зарегистрированным командам
        message = 'Игра началась!'
        send_to_all_admins(context, message)
        send_to_all_commands(context, message)


# Функция отправления следующего вопроса. Доступна только админам. Вызов /nextq
def next_question(update, context):
    # Получаем глобальную переменную текущего вопроса
    global current_question
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        # Проверяем теущее состояние игры
        if state == REGISTRATION:
            # Если регистрация ещё не закончилась
            context.bot.send_message(chat_id=chat_id, text='Дождитесь начала игры!')
        if state == IN_QUESTION:
            # Если предыдущий вопрос ещё не закончился
            context.bot.send_message(chat_id=chat_id, text='Дождитесь окончания вопроса!')
        if state == GAME:
            # Проверяем, есть ли номер текущего вопроса в вопросах (questions.keys())
            if current_question in questions.keys():
                # Меняем состояние игры на IN_QUESTION
                set_state(IN_QUESTION)
                # Достаём текст вопроса
                question_text = questions[current_question]
                # Отправляем текст вопроса всем зарегистрированным командам и администраторам
                send_to_all_commands(context, message=question_text)
                send_to_all_admins(context, message=question_text)
                # Ставим таймер на 50 секунд. По истечении времени вызовется функция alert_question c аргументом context
                # Функция предупредит зарегистрированные команды и админов о том, что осталось 20 секунд
                alert_timer = Timer(50.0, alert_question, [context])
                # Ставим таймер на 70 секунд. По истечении времени вызовется функция end_question с аргументом context
                # Функция завершит вопрос
                end_question_timer = Timer(70.0, end_question, [context])
                # Запускаем установленные таймеры
                alert_timer.start()
                end_question_timer.start()
            else:
                # Если вопроса с номером current_question не существует
                context.bot.send_message(chat_id=chat_id,
                                         text='Вопроса под номером ' + str(current_question) + ' не существует!')
                context.bot.send_message(chat_id=chat_id,
                                         text='Добавьте его с помощью команды /addq номер_вопроса текст_вопроса')
    else:
        # Если пользователь не является администратором
        context.bot.send_message(chat_id=chat_id, text="Вы не обладаете правами администратора!")


#Функция предупреждения о том, что до конца времени на вопрос осталось 20 секунд. Вызывается только из функции next_question по таймеру
def alert_question(context):
    # Отправляем зарегистрированным командам и админам сообщение о том, что осталось 20 секунд
    send_to_all_commands(context, message='Осталось 20 секунд!')
    send_to_all_admins(context, message='Осталось 20 секунд!')


#Функция конца вопроса. Вызвается только из функции next_question по таймеру
def end_question(context):
    #Получаем глобальную переменную номера вопроса
    global current_question
    #Отправляем зарегистрированным командам и админам сообщение о том, что время вышло
    send_to_all_commands(context, message='Время вышло!')
    send_to_all_admins(context, message='Время вышло!')
    # Прибавляем к номеру текущего вопроса 1
    current_question += 1
    # Меняем состояние игры с IN_QUESTION на GAME
    set_state(GAME)


#Функция для установки ссылки на турнирную таблицу. Доступна только админам. Вызов /set_table url
def set_table(update, context):
    chat_id = update.effective_chat.id
    global table_URL
    if check_admin(chat_id):
        if len(context.args) > 0:
            table_URL = context.args[0]
            context.bot.send_message(chat_id=chat_id, text="Ссылка на турнирную таблицу:\n" + table_URL)
        else:
            context.bot.send_message(chat_id=chat_id, text="Введите ссылку на турнирную таблицу в аргументах!")
    else:
        context.bot.send_message(chat_id=chat_id, text="Вы не обладаете правами администратора!")


#Функция для получения ссылки на турнирную таблицу. Доступна всем. Вызов /get_table
def get_table(update, context):
    chat_id = update.effective_chat.id
    global table_URL
    context.bot.send_message(chat_id=chat_id, text="Ссылка на турнирную таблицу:\n" + table_URL)


#Вывод списка команд для админов. Вывод ссылки на администратора для не админов. Вызов /help
def help(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    #Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        #Если является, высылаем список команд с их коротким описанием
        message = "Список команд для администратора:\n" \
                  "/addq номер_вопроса текст_вопроса - добавляет вопрос\n" \
                  "/getq - выводит все добавленные вопросы\n" \
                  "/clearq - удаляет все вопросы\n" \
                  "/getc - выводит список зарегистрированных команд\n" \
                  "/start_game - начинает игру (использовать только один раз)\n" \
                  "/nextq - высылает зарегистрированным пользователям следующий по порядку вопрос (порядок начинается с 0)," \
                  " стартует таймер на 1 мин 10 сек. После 50 сек высылает предупреждение 'Осталось 20 секунд'." \
                  " После 1 минуты высылается сообщение 'Время истекло!' " \
                  "Всю эту минуту сообщения зарегистрированных пользователей пересылаются вам\n" \
                  "/set_table ссылка - установить ссылку на турнирную таблицу\n" \
                  "/sendcom сообщение - отправить сообщение всем зарегистрированным командам\n" \
                  "/sendadm сообщение - отправить сообщение всем администраторам\n" \
                  "/sendall сообщение - отправить сообщение всем администраторам и зарегистрированным командам"
        context.bot.send_message(chat_id=chat_id, text=message)
    else:
        #Если пользоавтель не является админам, высылаем ему ссылку на администратора (ADMIN_LINK)
        context.bot.send_message(chat_id=chat_id,
                                 text="По всем техническим вопросам пишите администратору:\n" + ADMIN_LINK)


#Функция пропуска вопроса. Доступна только админам. Вызов /skipq
def skip_question(update, context):
    #Получаем глобальную переменную номера теущего вопроса
    global current_question
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        #Если является, добавляем к номеру текущего вопроса 1, высылваем сообщение о том, что вопрос пропущен
        current_question += 1
        message = "Пропущен вопрос номер " + str(current_question - 1)
        send_to_all_admins(context, message)
    else:
        #Если пользователь не является администраторам, сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id, text="Вы не обладаете правами администратора")


#Функция для отправления сообщения всем зарегистрированным командам. Только для админов. Взов /sendcom Текст сообщения
def send_to_commands_command(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        #Проверяем, введён ли текст сообщения в аргументы
        if len(context.args) > 0:
            # Формируем сообщения, отправляем его всем командам
            message = 'Сообщение от администратора:\n' + ' '.join(context.args)
            send_to_all_commands(context, message)
            context.bot.send_message(chat_id=chat_id, text="Сообщение отправлено всем командам")
        else:
            # Если текст сообщения не введён, пишем об этом пользователю
            context.bot.send_message(chat_id=chat_id, text="Введите сообщение!")
    else:
        #Если пользователь не является администратором, сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id, text="Вы не обладаете правами администратора")


#Функция для отправления сообщения всем админам. Только для админов. Взов /sendadm Текст сообщения
def send_to_admins_command(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        #Проверяем, введён ли текст сообщения в аргументы
        if len(context.args) > 0:
            # Формируем сообщения, отправляем его всем админам
            message = 'Сообщение от администратора:\n' + ' '.join(context.args)
            send_to_all_admins(context, message)
            context.bot.send_message(chat_id=chat_id, text="Сообщение отправлено всем администраторам")
        else:
            # Если текст сообщения не введён, пишем об этом пользователю
            context.bot.send_message(chat_id=chat_id, text="Введите сообщение!")
    else:
        #Если пользователь не является администратором, сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id, text="Вы не обладаете правами администратора")


#Функция для отправления сообщения всем. Только для админов. Взов /sendall Текст сообщения
def send_to_all_command(update, context):
    # Записываем id, из которого пришло сообщение
    chat_id = update.effective_chat.id
    # Проверяем, является ли пользователь админом
    if check_admin(chat_id):
        #Проверяем, введён ли текст сообщения в аргументы
        if len(context.args) > 0:
            # Формируем сообщения, отправляем его всем админам
            message = 'Сообщение от администратора:\n' + ' '.join(context.args)
            send_to_all_admins(context, message)
            send_to_all_commands(context, message)
            context.bot.send_message(chat_id=chat_id,
                                     text="Сообщение отправлено всем администраторам и зарегистрированным командам")
        else:
            # Если текст сообщения не введён, пишем об этом пользователю
            context.bot.send_message(chat_id=chat_id, text="Введите сообщение!")
    else:
        #Если пользователь не является администратором, сообщаем ему об этом
        context.bot.send_message(chat_id=chat_id, text="Вы не обладаете правами администратора")


#Функция отправления сообщения всем (не путать с send_to_all_command)
def send_to_all(context, message):
    for user_id in users_statuses.keys():
        context.bot.send_message(chat_id=user_id, text=message)


#Функция отправления сообщения всем зарегистрированным командам (не путать с send_to_commands_command)
def send_to_all_commands(context, message):
    for command_id in command_numbers.keys():
        context.bot.send_message(chat_id=command_id, text=message)

#Функция отправления сообщения всем админам (не путать с send_to_admins_command)
def send_to_all_admins(context, message):
    for user_id in users_statuses.keys():
        if users_statuses[user_id] == ADMIN:
            context.bot.send_message(chat_id=user_id, text=message)


# Функция проверки, является ли пользователь администратором.
def check_admin(chat_id):
    #Проверяем, есть ли у пользователя, который нам написал какой-либо статус
    if chat_id in users_statuses.keys():
        #Если есть, проверяем, является ли этот статус статусом ADMIN. Если да, функция вернёт True, иначе False.
        return users_statuses[chat_id] == ADMIN
    else:
        #Если у пользователя нет статуса, устанавливаем ему статус GUEST. В этом случае функция вернёт False
        users_statuses[chat_id] = GUEST
        return False


# Функция установки состояния игры
def set_state(new_state):
    global state
    state = new_state


# Функция, которая запускается при запуске бота
def main():
    #Для каждой команды сначала создаём handler, который будет "держать" саму команду и функцию, которая должна вызываться при вызове команды из бота.
    #Пример:
    #Команда помощи вызывается по сообщению /help (пишем 'help' первым аргументом)
    #При написании /help должна вызваться функция help, которую мы передаём вторым аргументом
    help_handler = CommandHandler('help', help)
    #Созданный handler мы добавляем в dispatcher, который автоматически будет вызывать функцию help, когда боту придёт сообщение /help
    dispatcher.add_handler(help_handler)

    #Аналогично всё делаем для отсальных команд
    send_to_commands_command_handler = CommandHandler('sendcom', send_to_commands_command)
    dispatcher.add_handler(send_to_commands_command_handler)

    send_to_admins_command_handler = CommandHandler('sendadm', send_to_admins_command)
    dispatcher.add_handler(send_to_admins_command_handler)

    send_to_all_command_handler = CommandHandler('sendall', send_to_all_command)
    dispatcher.add_handler(send_to_all_command_handler)

    set_table_handler = CommandHandler('set_table', set_table)
    dispatcher.add_handler(set_table_handler)

    get_table_handler = CommandHandler('get_table', get_table)
    dispatcher.add_handler(get_table_handler)

    #Для некоторых команд для удобства сделано по 2 handler-а, чтобы можно было писать одну команду по разному
    #Например команда для регистрации может быть двумя способами: /registration command_name или /reg command_name
    command_registration_handler = CommandHandler('registration', command_registration)
    dispatcher.add_handler(command_registration_handler)

    command_registration_handler_2 = CommandHandler('reg', command_registration)
    dispatcher.add_handler(command_registration_handler_2)

    next_question_handler = CommandHandler('next_question', next_question)
    dispatcher.add_handler(next_question_handler)

    next_question_handler2 = CommandHandler('nextq', next_question)
    dispatcher.add_handler(next_question_handler2)

    start_game_handler = CommandHandler('start_game', start_game)
    dispatcher.add_handler(start_game_handler)

    get_commands_handler = CommandHandler('get_commands', get_commands)
    dispatcher.add_handler(get_commands_handler)

    get_commands_handler_2 = CommandHandler('getc', get_commands)
    dispatcher.add_handler(get_commands_handler_2)

    enter_admin_mode_handler = CommandHandler('admin', enter_admin_mode)
    dispatcher.add_handler(enter_admin_mode_handler)

    add_question_handler = CommandHandler('add_question', add_question)
    dispatcher.add_handler(add_question_handler)

    add_question_handler_2 = CommandHandler('addq', add_question)
    dispatcher.add_handler(add_question_handler_2)

    get_questions_handler = CommandHandler('get_questions', get_questions)
    dispatcher.add_handler(get_questions_handler)

    get_questions_handler_2 = CommandHandler('getq', get_questions)
    dispatcher.add_handler(get_questions_handler_2)

    skip_question_handler = CommandHandler('skipq', skip_question)
    dispatcher.add_handler(skip_question_handler)

    clear_questions_handler = CommandHandler('clearq', clear_questions)
    dispatcher.add_handler(clear_questions_handler)

    # Это особенный handler, который вызывает функцию по сообщению. Он проверяет, является ли сообщение текстом и НЕ командой
    # Если условие не выполняется, вызывается функция get_message
    get_message_handler = MessageHandler(Filters.text & (~Filters.command), get_message)
    dispatcher.add_handler(get_message_handler)

    print("Бот запущен!")
    # Вызываем у updater, котрый мы получили по токену бота почти в самом начале кода, функцию принятия сообщений
    updater.start_polling()


if __name__ == '__main__':
    main()
