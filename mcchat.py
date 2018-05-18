# ~/.virtualenvs/mc-bot/bin/python3 ~/.virtualenvs/mc-bot/mcchat.py

from pygtail import Pygtail
import time
import re
import logging
import os
from subprocess import check_output, run, PIPE
from datetime import datetime
import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import Unauthorized
from telegram import ParseMode
from settings import Settings


# Setting up internal logging system
# for output to file, add: filename='mc-bot.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - \
                            %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Remove ansi decorations
def _ansi_escape(input_text):
    output = re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{1,2})?)?[m|K]?', '', input_text)
    output = re.sub(r'\r|\n', '', output)
    logger.debug('_ansi_escape: ' + output)
    return output


def _send_command(command, arg=''):
    logger.info('Sending command {} to minecraft process'.format(command))
    command_to_call = ['minecraftd', 'command', command, arg]
    output = run(command_to_call, check=True, stdout=PIPE)
    logger.debug('Server returned: ' + str(output))
    if output.returncode == 0:
        logger.info('Command sent')
        out = _ansi_escape(output.stdout.decode('utf-8'))
        logger.debug('Escaped output string: ' + out)
        return out
    else:
        logger.warning('Command hasn\'t been sent because of error')


# Get chats to where we will send updates
def _get_all_chats():
    # Open database
    conn = sqlite3.connect(Settings.database)
    conn.row_factory = lambda cursor, row: row[0]
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_subscribe')
    all_chats = cursor.fetchall()
    conn.close()
    logger.info('[DB] Chats to send {}'.format(all_chats))
    return all_chats


def _db_query(query):
    result = {}
    # Open database
    logger.info('Connecting to DB with query: ' + query)
    conn = sqlite3.connect(Settings.database)
    cursor = conn.cursor()
    for row in cursor.execute(query):
        result.update({row[0]: row[1]})
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()
    return result


def _db_update(query):
    logger.info('Connecting to DB with query: ' + query)
    conn = sqlite3.connect(Settings.database)
    c = conn.cursor()
    c.execute(query)
    # Save (commit) the changes
    conn.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


def _mc_time():
    reply = _send_command('time', 'query daytime')
    logger.debug('Time in mc is ' + reply)
    split = re.findall(r'Time is ([0-9]+).+', reply)
    ctime = (int(split[0]) / 24000 * 24 + 6) * 60 * 60
    out = time.strftime('%H:%M:%S', time.gmtime(ctime))
    return str(out)


def _log_inode():
    return os.stat(Settings.log_file).st_ino


def mc_time(bot, update):
    logger.info('User {} send comand /time'.
                format(update.message.from_user.id))
    out = _mc_time()
    update.message.reply_text('Ingame time: ' + out)


def tps(bot, update):
    logger.info('User {} send comand /tps'.
                format(update.message.from_user.id))
    reply = _send_command('tps')
    split = re.findall(r'([0-9]+.[0-9]+) TPS.+', reply)
    update.message.reply_text('Overall TPS: ' + str(split[0]))


def user_list(bot, update):
    logger.info('User {} send comand /list'.
                format(update.message.from_user.id))
    reply = _send_command('list')
    split = re.findall(r'There are ([0-9]+/[0-9]+).+', reply)
    update.message.reply_text('Total online: ' + split[0])


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def start(bot, update):
    logger.info('User {} send comand /start'.
                format(update.message.from_user.id))
    update.message.reply_text('Hi!')


def bot_help(bot, update):
    logger.info('User {} send comand /help'.
                format(update.message.from_user.id))
    reply = """Cписок доступных команд:
/help - помощь
/tps - текущее значение TPS
/list - список игроков онлайн
/time - текущее внутриигровое время
/usage - загрузка ЦПУ и памяти
/subscribe - подписаться на обновления чата. Бот будет присылать сообщения из игры, вы сможете отправлять сообщения в игровой чат
/unsubscribe - отписаться от обновлений чата
/map - ссылка на карту
/files - ссылка на модпак
/money - помочь деньгами на содержание сервера ❤
"""
    update.message.reply_text(reply)


def user_id(bot, update):
    logger.info('User {} send comand /id'.
                format(update.message.from_user.id))
    reply = update.message.chat_id
    update.message.reply_text('Chat ID: ' + str(reply))


def subscribe(bot, update):
    logger.info('User {} send comand /subscribe'.
                format(update.message.from_user.id))
    # chat.id is equal to from_user.id if it's private channel
    # so we will use it
    chat_id = update.message.from_user.id
    if chat_id not in Settings.banned_chats:
        update.message.reply_text('Вы подписаны на обновления чата. \
Бот будет автоматически присылать обновления. Чтобы отписаться от \
обновлений отправьте /unsubscribe')
        _db_update('INSERT OR IGNORE INTO chat_subscribe VALUES ({})'.
                   format(chat_id))
    else:
        update.message.reply_text('Сорри, но этот чат \
подписать нельзя.')


def unsubscribe(bot, update):
    logger.info('User {} send comand /unsubscribe'.
                format(update.message.from_user.id))
    chat_id = update.message.chat_id
    update.message.reply_text('Вы отписались от обновлений чата. \
Чтобы снова подписаться на обновления отправьте /subscribe')
    _db_update('DELETE FROM chat_subscribe WHERE uid=\'{}\''.format(chat_id))


def exmap(bot, update):
    logger.info('User {} send comand /map'.
                format(update.message.from_user.id))
    reply = Settings.map_link
    update.message.reply_text(reply)


def mods(bot, update):
    logger.info('User {} send comand /mods'.
                format(update.message.from_user.id))
    reply = "Мы играем в {}. Скачать можно по ссылке: {}".format(Settings.modpack_name, Settings.modpack_url)
    update.message.reply_text(reply)


def money(bot, update):
    logger.info('User {} send comand /money'.
                format(update.message.from_user.id))
    reply = "Помочь денежкой на содержание сервера: {} \n\
Последние транзакции:\n".format(Settings.donate_to)
    # Open database
    conn = sqlite3.connect(Settings.database)
    c = conn.cursor()
    for row in c.execute('SELECT * FROM stocks ORDER BY date desc LIMIT 10'):
        reply = reply + str(row) + "\n"
    conn.close()
    update.message.reply_text(reply)


def add_money(bot, update, args):
    logger.info('User {} send comand /add_money'.
                format(update.message.from_user.id))
    if args and len(args) == 3:
        # Open database
        conn = sqlite3.connect(Settings.database)
        c = conn.cursor()
        # Insert data
        today = datetime.today()
        date = today.strftime("%Y-%m-%d")
        c.execute("INSERT INTO stocks VALUES ('" + date + "', ?, ?, ?)", args)
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()
        reply = 'Добавлено: ' + str(args)
        update.message.reply_text(reply)
    else:
        reply = "/add_money @NICKNAME CURRENCY AMOUNT"
        update.message.reply_text(reply)


def usage(bot, update):
    logger.info('User {} send comand /usage'.
                format(update.message.from_user.id))
    mem = check_output(r'free -m | sed -n "s/^Mem:\s\+[0-9]\+\s\+\([0-9]\+\)\s.\+/\1/p"', shell=True).decode('utf-8')
    hdd = check_output(r"df -h | sed -n 4p | awk '{ print $4 }'", shell=True).decode('utf-8')
    uptime = check_output('uptime -p', shell=True).decode('utf-8')
    output = "Free RAM, Mb: {}Free HDD: {}\
Uptime: {}".format(mem, hdd, uptime)
    bot.sendMessage(chat_id=update.message.chat_id, text=output)


def to_mc_chat(bot, update):
    all_chats = _get_all_chats()
    user_id = update.message.from_user.id
    chat_id = str(update.message.chat_id)
    if chat_id not in all_chats:
        logger.info('Chat {} not in all_chats list: {}'.
                    format(chat_id, all_chats))
        subscribe(bot, update)
    mc_name = Settings.mc_users[update.message.from_user.username]
    text = update.message.text
    logger.info('User {} ({}) send plain text: {}'.
                format(user_id, mc_name, text))
    say = r'say §3[TG]§r<{}> {}'.format(mc_name, text)
    _send_command('say', say)
    tg_text = '{}: {}'.format(mc_name, text)
    logger.info('Send message for other subscribers')
    all_chats.remove(chat_id)
    if len(all_chats) > 0:
        for chat_id in all_chats:
            bot.send_message(chat_id=chat_id,
                             text=tg_text, parse_mode=ParseMode.MARKDOWN)


def read_log(bot, job):
    global initial_log_inode
    # For tests we are using logs/latest.log file
    # f = open('logs/latest.log', encoding='utf8')
    # for line in f.readlines():
    log_inode = _log_inode()
    if log_inode != initial_log_inode:
        logger.debug("Current log.offset inode {} \
is different with initial inode {}. \
Log rotated.".format(log_inode, initial_log_inode))
        os.remove(Settings.log_offset)
        initial_log_inode = log_inode
    for line in Pygtail(Settings.log_file, offset_file=Settings.log_offset):
            regex = None
            action = None
            # logger.debug(line)
            for action in Settings.actions:
                if Settings.actions[action].match(line):
                    regex = Settings.actions[action]
                    break
            if regex is not None:
                data = regex.split(line)
                logger.debug('{}: {}'.format(action, data))
                send_to_telegram(bot, action, data)


def send_to_telegram(bot, action, data):
    all_chats = _get_all_chats()
    # Telegram notification
    logger.info('Sending notification to telegram chats')
    if action == 'server_stop':
        text = '`Сервер остановлен!`'
    elif action == 'server_start':
        text = '`Сервер стартовал!`'
    elif action == 'death':
        text = '{} _умер!_'.format(data[4])
    elif action == 'advancement':
        text = '{} _получил ачивку [{}]_'.format(data[4], data[7])
    elif action == 'login':
        text = '{} _вошел в игру_'.format(data[4])
    elif action == 'logout':
        text = '{} _вышел из игры_ ({})'.format(data[4], data[5])
    elif action == 'chat_message':
        text = '{}: _{}_'.format(data[5], data[7])
    for chat_id in all_chats:
        try:
            bot.send_message(chat_id=chat_id,
                             text=text, parse_mode=ParseMode.MARKDOWN)
        except Unauthorized:
            logger.warn('User {} banned our bot, going to unsubscribe him'.format(chat_id))
            _db_update('DELETE FROM chat_subscribe WHERE uid=\'{}\''.format(chat_id))


def main():
    logger.info('Starting!')

    updater = Updater(Settings.tg_token)
    dp = updater.dispatcher
    j = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", bot_help))
    dp.add_handler(CommandHandler("id", user_id))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("tps", tps))
    dp.add_handler(CommandHandler("list", user_list))
    dp.add_handler(CommandHandler("time", mc_time))
    dp.add_handler(CommandHandler("map", exmap))
    dp.add_handler(CommandHandler("mods", mods))
    dp.add_handler(CommandHandler("version", mods))
    dp.add_handler(CommandHandler("pack", mods))
    dp.add_handler(CommandHandler("files", mods))
    dp.add_handler(CommandHandler("modpack", mods))
    dp.add_handler(CommandHandler("usage", usage))
    dp.add_handler(CommandHandler("money", money))
    dp.add_handler(CommandHandler("add_money", add_money, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text, to_mc_chat))
    """
    # User restricted actions
    u_handler = CommandHandler('unload', unload,
                           filters=Filters.user
                           (user_id=Settings.las_readers),
                           pass_args=True)
    """
    j.run_repeating(read_log,
                    interval=5,
                    first=0)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    initial_log_inode = _log_inode()
    main()
