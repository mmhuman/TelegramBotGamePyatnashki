# -*- coding: utf-8 -*-
import config
import telebot
import random
import logging
import sys

MOVE_UP = 0
MOVE_RIGHT = 1
MOVE_DOWN = 2
MOVE_LEFT = 3

MIN_FIELD_SIZE = 2
MAX_FIELD_SIZE = 16


try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("bot_info")
    handler = logging.FileHandler("bot_info.log")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Start logging')
except Exception as e:
    print("Logging initialization failed")
    print(e)
    sys.exit()


try:
    bot = telebot.TeleBot(config.token)
except Exception as e:
    logger.info("Bot initialization failed")
    logger.info(e)
    sys.exit()


class Game15:
    def __init__(self, n):
        self.n = n
        self.field = [[0] * n for i in range(n)]
        for i in range(n):
            for j in range(n):
                self.field[i][j] = i * n + j + 1
        self.field[n - 1][n - 1] = 0
        self.sol = ''
        self.shuffle()

    def shuffle(self):
        MOVES_TO_SHUFFLE = min(1000, self.n * self.n * self.n)
        for i in range(MOVES_TO_SHUFFLE):
            move_num = random.randint(0, 3)
            self.move(move_num)

    def move(self, move_num):
        if (move_num < 0 or move_num > 3):
            return -1
        flag = True
        for i in range(self.n):
            for j in range(self.n):
                if (self.field[i][j] == 0 and flag):
                    ti = i
                    tj = j
                    if (move_num == 0):
                        ti += 1
                    if (move_num == 1):
                        tj -= 1
                    if (move_num == 2):
                        ti -= 1
                    if (move_num == 3):
                        tj += 1
                    if (ti < 0 or ti >= self.n or tj < 0 or tj >= self.n):
                        return -1
                    self.field[i][j], self.field[ti][tj] =\
                        self.field[ti][tj], self.field[i][j]
                    flag = False

        back_moves = ['s', 'a', 'w', 'd']
        self.sol = back_moves[move_num] + self.sol


class Chat:
    def __init__(self):
        self.is_game_started = 0

    def start_game(self, n):
        self.is_game_started = 1
        self.game = Game15(n)


dict_chats = dict()


def safe_send_message(chat_id, msg):
    try:
        bot.send_message(chat_id, msg)
    except Exception as e:
        logger.info("Send messege failed")
        logger.info("%s", str(e))


def user_init(id):
    if (dict_chats.get(id) is None):
        dict_chats[id] = Chat()
        logger.info("User %s initialized", str(id))


@bot.message_handler(regexp="^/start")
def start(message):
    user_init(message.chat.id)
    command = message.text.split('@')[0]
    chat = dict_chats[message.chat.id]
    if (len(command) < 6 or not(command[6:].isdecimal())):
        n = 4
    else:
        n = int(command[6:])
    if (n >= MIN_FIELD_SIZE and n <= MAX_FIELD_SIZE):
        logger.info("User %s start new game %s x %s", message.chat.id, n, n)
        chat.start_game(n)
    else:
        wrong_command(message)
        return -1
    safe_send_message(message.chat.id, "Game started")
    print_field(message.chat.id)


@bot.message_handler(commands=["help"])
def help(message):
    user_init(message.chat.id)
    safe_send_message(message.chat.id, """commands:
/startN - start game with field N x N (N >= 2 and N <= 16)
/w, /a, /s, /d, w, a, s, d - commands that move tiles
/end_game - finish game
/solve - print move sequence that solves the puzzle
If you notice bugs contact with me in:
vk.com/id205067947 ,
Telegram @mHuman""")


@bot.message_handler(commands=['w', 'd', 's', 'a'])
def move(message):
    user_init(message.chat.id)
    if (dict_chats[message.chat.id].is_game_started == 0):
        safe_send_message(message.chat.id, "Game isn't started yet")
        return -1
    chat = dict_chats[message.chat.id]
    moves = {'w': MOVE_UP, 'd': MOVE_RIGHT, 's': MOVE_DOWN, 'a': MOVE_LEFT}
    chat.game.move(moves[message.text[1]])
    print_field(message.chat.id)


@bot.message_handler(commands=["end_game"])
def end_game(message):
    user_init(message.chat.id)
    if (dict_chats[message.chat.id].is_game_started == 0):
        safe_send_message(message.chat.id, "Game isn't started yet")
        return -1
    chat = dict_chats[message.chat.id]
    chat.is_game_started = 0


def print_field(chat_id):
    user_init(chat_id)
    if (dict_chats[chat_id].is_game_started == 0):
        return -1
    chat = dict_chats[chat_id]
    answer = ""
    max_l = len(str(chat.game.n * chat.game.n - 1))
    for a in chat.game.field:
        for b in a:
            l = len(str(b))
            answer = answer + str(b)
            while l <= max_l:
                answer = answer + "  "
                l += 1
        answer = answer + '\n'
    safe_send_message(chat_id, answer)


@bot.message_handler(commands=["solve"])
def solve(message):
    user_init(message.chat.id)
    if (dict_chats[message.chat.id].is_game_started == 0):
        safe_send_message(message.chat.id, "Game isn't started yet")
        return -1
    chat = dict_chats[message.chat.id]
    solution = ""
    for x in chat.game.sol:
        solution = solution + x
    logger.info("User %s ask to solve game %s x %s",
                message.chat.id, chat.game.n, chat.game.n)
    safe_send_message(message.chat.id, solution)


@bot.message_handler(content_types=["text"])
def wrong_command(message):
    user_init(message.chat.id)
    if (message.text[0] in ['w', 'd', 's', 'a'] and len(message.text) == 1):
        message.text = "/" + message.text
        move(message)
        return
    safe_send_message(message.chat.id, message.text + " is wrong command")


if __name__ == '__main__':
    random.seed()
    bot.polling(none_stop=True)
