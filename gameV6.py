import os
import sys
from datetime import datetime
import pygame
from random import choice
from time import sleep
import schedule
import sqlite3


def load_image(name, color_key=None):
    fullname = os.path.join('data/image', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


def save():
    for i in range(0, 4):
        cur.execute(f"""Update main set level_{i + 1} = '{progress[i]}' where id = 1""")
        con.commit()


WIDTH, HEIGHT = 500, 500
level_completed = {}
for n in range(1, 5):
    exec(f'keys_{n} = {n * 5}')
    level_completed[eval(f'keys_{n}')] = n
    exec(
        f"level_{n} = list(map(str.strip, open(f'data/levels/level_0{n}.map', mode='r', encoding='utf8').readlines()))")
locked_levels = {'2': 92, '3': 180, '4': 267}
tile_width = tile_height = 50
door = ''


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, image, side, sign):
        super().__init__(tiles, all_sprites)
        self.sign = sign
        self.image = image
        self.side = side
        self.abs_pos = [pos_x, pos_y]
        self.rect = self.image.get_rect().move(
            self.side * pos_x, self.side * pos_y)

    def process(self, signs):
        return self.sign in signs


class Button:
    def __init__(self, pos_x, pos_y, side_x, side_y):
        self.abs_pos = [pos_x, pos_y]
        self.side_x, self.side_y = side_x, side_y

    def intersection(self, pos):
        return (self.abs_pos[0] <= pos[0] <= (self.abs_pos[0] + self.side_x)) and (
                self.abs_pos[1] <= pos[1] <= (self.abs_pos[1] + self.side_y))

    def next(self, step, value):
        temp = value + step
        return temp if (0 < temp < 5) else value


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, image, side):
        super().__init__(player, all_sprites)
        self.image = image[0]
        self.image1 = image[1]
        self.flips = 0
        self.side = side
        self.rect = self.image.get_rect().move(
            self.side * pos_x + 15, self.side * pos_y + 5)
        self.pos = (pos_x, pos_y)
        self.draw_pos = (pos_x, pos_y)

    def move(self, dx, dy, obj):
        self.pos = (dx + self.pos[0], dy + self.pos[1])
        # смещение персонажа
        if obj == 'player':
            self.draw_pos = (self.draw_pos[0] + dx, self.draw_pos[1] + dy)
            self.rect = self.image.get_rect().move(self.side * self.draw_pos[0] + 15, self.side * self.draw_pos[1] + 5)
        # смещение камеры
        elif obj == 'camera':
            camera.dx -= tile_width * dx
            camera.dy -= tile_height * dy
            for tile in tiles:
                camera.apply(tile)

    def update(self):
        self.flips += 0.25
        if self.flips == 10 or self.flips == 11:
            self.image, self.image1 = self.image1, self.image
        if self.flips == 11:
            self.flips = 0


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x = obj.rect.x + self.dx
        obj.rect.y = obj.rect.y + self.dy

    def update(self):
        self.dx = 0
        self.dy = 0


class Board:
    def __init__(self, side, map_):
        self.cell = [[0] * HEIGHT for i in range(WIDTH)]
        self.borders = ['#']
        self.fall = False
        # механизм добавки ячеек, через которые нельзя проходить / пока нету /
        self.exit_pos = (0, 0)
        self.images = {
            '#': load_image('wall.png'),
            '.': load_image('floor.png'),
            'p': [load_image('player.png'), load_image('player1.png')],
            'o': load_image('hole.png'),
            'm': load_image('key.png'),
            'e': load_image('door.png'),
            'i': load_image('door.png')}
        if len(door):
            self.images['e'] = load_image(door)
        for y in range(len(map_)):
            for x in range(len(map_[0])):
                if map_[y][x] == 'p':
                    self.cell[x][y] = Tile(x, y, self.images['.'], side, '.')
                    self.player = Player(x, y, self.images['p'], side)
                else:
                    self.cell[x][y] = Tile(x, y, self.images[map_[y][x]], side, map_[y][x])
                if map_[y][x] == 'e':
                    self.exit_pos = (x, y)

        self.WIDTH_IN_CAGES = x - 1
        self.HEIGHT_IN_CAGES = y - 1

    def move(self, x, y):
        global not_is_exit
        pos = self.player.pos
        draw_pos = self.player.draw_pos
        if self.cell[pos[0] + x][pos[1] + y].sign == 'o':
            self.fall = True
        elif self.cell[pos[0] + x][pos[1] + y].sign == 'i':
            not_is_exit = ("Я отсюда пришёл.", 180)
        elif not self.cell[pos[0] + x][pos[1] + y].process(self.borders):
            # проверка на то, что лучше сместить: камеру или персонажа
            check_move = x or y
            check_pos = pos[0] if x else pos[1]
            check_d_pos = draw_pos[0] if x else draw_pos[1]
            max_pos = (self.WIDTH_IN_CAGES if x else self.HEIGHT_IN_CAGES) - 3
            if not (4 < check_pos < max_pos) or (check_d_pos in [4, 5] and check_d_pos + check_move in [4, 5]):
                self.player.move(x, y, 'player')
            else:
                self.player.move(x, y, 'camera')
        if not_is_exit and self.cell[pos[0] + x][pos[1] + y].sign != 'i':
            not_is_exit = ('', 10)


def terminate():
    pygame.quit()
    sys.exit()


def check_door(door_is_open, cell_is_door):
    return (not cell_is_door) or (door_is_open and cell_is_door)


def game_timer():
    global game_time
    game_time += 1


def game(WIDTH, HEIGHT):
    global music_on, players_keys, not_is_exit, game_time
    # инициализация окна
    pygame.init()
    size = WIDTH, HEIGHT
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('The Walls')
    lst_of_track = os.listdir('data/music/game music')
    running_track = -1
    final_sound = pygame.mixer.Sound("data/music/steps_sound.wav")
    # инициализация объектов
    board = Board(50, _map)
    game_time = 0
    # счётчик ключей
    players_keys = 0
    keys_color = (255, 0, 0)
    key_sound = pygame.mixer.Sound("data/music/take_key.wav")
    door_is_open = False
    door_opening_sound = pygame.mixer.Sound("data/music/opening_door.wav")
    not_is_exit = ("", 50)
    # фокус на персонажа
    pos = board.player.pos
    dx = board.WIDTH_IN_CAGES - 8 if (n := (pos[0] - 4 if pos[0] - 4 > 0 else 0)) > board.WIDTH_IN_CAGES - 8 else n
    dy = board.HEIGHT_IN_CAGES - 8 if (n := (pos[1] - 4 if pos[1] - 4 > 0 else 0)) > board.HEIGHT_IN_CAGES - 8 else n
    camera.dx -= tile_width * dx
    camera.dy -= tile_height * dy
    for tile in tiles:
        camera.apply(tile)
    # сдвиг игрока относительно положения камеры
    board.player.draw_pos = (board.player.draw_pos[0] - dx, board.player.draw_pos[1] - dy)
    board.player.rect = board.player.image.get_rect().move(board.player.side * board.player.draw_pos[0] + 15,
                                                           board.player.side * board.player.draw_pos[1] + 5)
    # игровой цикл / игра началась
    game_position = 'game_on'
    running = False
    # параметры для затемнения окна
    opening = True
    darken_percent = 0.99
    dark = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
    # пауза
    pause = False
    while running or opening:
        player_pos = board.player.pos
        if running and not pause:
            schedule.run_pending()
        for event in pygame.event.get():
            if running:
                if game_position == 'game_on':
                    if event.type == pygame.QUIT:
                        return 0
                    # Пауза/пуск если окно игры не в фокусе
                    if event.type in [pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST]:
                        pause = not pause
                        pygame.mixer.music.set_volume(0.5 if pygame.mixer.music.get_volume() == 1 else 1)

                    elif event.type == pygame.KEYDOWN:
                        move_dct = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
                                    pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}
                        if event.key in move_dct and not pause:
                            e = event.key
                            # Движение
                            if check_door(door_is_open, board.cell[player_pos[0] + move_dct[e][0]][
                                player_pos[1] + move_dct[e][1]].process(['e'])):
                                board.move(*move_dct[e])
                            # Бьёшься головой об дверь
                            elif not door_is_open and board.cell[player_pos[0] + move_dct[e][0]][
                                player_pos[1] + move_dct[e][1]].process(['e']):
                                not_is_exit = (f"Заперто. Нужно найти ещё {keys - players_keys} ключей.", 100)
                        # Вкл/выкл музыки
                        elif event.key == pygame.K_k:
                            pygame.mixer.music.stop() if music_on else pygame.mixer.music.play()
                            music_on = not music_on
                        # Выход в главное меню
                        elif event.key == pygame.K_ESCAPE:
                            pygame.mixer.music.stop()
                            return 1
                        # Пауза/пуск
                        elif event.key == pygame.K_SPACE:
                            pause = not pause
                            pygame.mixer.music.set_volume(0.5 if pause else 1)
                        # Рестарт
                        elif event.key == pygame.K_r:
                            pygame.mixer.music.stop()
                            return _map
                elif game_position == 'mini_game':
                    board, screen, game_position, running = mini_game(board, screen, game_position)
        # Если наступил на ключ
        if board.cell[player_pos[0]][player_pos[1]].process(['m']):
            board.cell[player_pos[0]][player_pos[1]].image = board.images['.']
            board.cell[player_pos[0]][player_pos[1]].sign = '.'
            players_keys += 1
            if music_on:
                pygame.mixer.Sound.play(key_sound)
            # Проверка все ли ключи были собраны
            if players_keys == keys:
                keys_color = (0, 255, 0)
                door_is_open = True
                if music_on:
                    pygame.mixer.Sound.play(door_opening_sound)
                board.cell[board.exit_pos[0]][board.exit_pos[1]].image = load_image('door_open.png')
                # Дверь на выход, если это последний уровень
                if len(door):
                    board.cell[board.exit_pos[0]][board.exit_pos[1]].image = load_image('door_open(exit).png')

        elif board.fall:
            if choice([1, 1, 0, 0, 0, 0, 0]):
                game_position = 'mini_game'
                board.fall = False
            else:
                running = False
                game_position = 'game_over'
        elif board.cell[player_pos[0]][player_pos[1]].process(['e']):
            running = False
            game_position = 'game_won'
        screen.fill(pygame.Color(0, 0, 0))
        if game_position == 'game_on':
            # отрисовка карты
            tiles.update(board.player.pos)
            tiles.draw(screen)
            # отрисовка персонажа
            player.draw(screen)
            camera.update()
            # отрисовка счётчика
            image = load_image('keys_counter.png')
            position_art = image.get_rect()
            screen.blit(image, position_art)
            font = pygame.font.SysFont('Ariel', 25)
            text = font.render(str(players_keys), True, keys_color)
            screen.blit(text, (26, 5))
            # отрисовка времени игры
            text = font.render(f'{game_time // 60}:{game_time % 60:0>2}', True, keys_color)
            screen.blit(text, (460 - 10 * (len(str(game_time // 60)) - 1), 5))
            # строка сообщений
            font_ms = pygame.font.Font(None, 25)
            text_ms = font_ms.render(not_is_exit[0], True, (255, 0, 0))
            screen.blit(text_ms, (not_is_exit[1], 5))
            # отрисовка паузы (если игра приостановлена)
            if pause:
                dark.fill((0, 0, 0, 0.5 * 255))
                screen.blit(dark, (0, 0))
                image = load_image('pause.png')
                position_art = image.get_rect()
                screen.blit(image, (220, 220))
                n = 0
                for i in ['Нажмине "пробел", чтобы продолжить.', 'Нажмине "escape", чтобы выйти.']:
                    text = font.render(i, True, 'white')
                    screen.blit(text, (90 + n * 25, 300 + n * 25))
                    n += 1
        # затемнение окна
        if opening:
            darken_percent = round(darken_percent - 0.01, 2)
            dark.fill((0, 0, 0, darken_percent * 255))
            screen.blit(dark, (0, 0))
            if music_on:
                pygame.mixer.music.set_volume(1 - darken_percent)
            if darken_percent == 0:
                running = True
                opening = False
        # Переключение трека, если закончилась музыка
        if music_on and not pygame.mixer.music.get_busy():
            running_track = (running_track + 1) % len(lst_of_track)
            pygame.mixer.music.load('data/music/game music/' + lst_of_track[running_track])
            pygame.mixer.music.play()

        pygame.display.flip()
        if not pause:
            player.update()
        clock.tick(20 if running else 50)
    pygame.mixer.music.set_volume(1)
    pygame.mixer.music.stop()
    # Выигрышная кат-сцена в конце
    if len(door) and game_position == 'game_won':
        cast_count = 1
        image = load_image(f'cast_scene{cast_count}.png')
        position_art = image.get_rect()
        game_time_str = f'{game_time // 60}:{game_time % 60:0>2}'
        if music_on:
            game_sound = pygame.mixer.Sound("data/music/game_won_sound.wav")
        if progress[level_completed[keys] - 1] == '∞' or \
                datetime.strptime(game_time_str, '%M:%S') < datetime.strptime(progress[level_completed[keys] - 1], '%M:%S'):
            progress[level_completed[keys] - 1] = game_time_str
            save()
    # Экран победы (со счётом) + музыка
    elif game_position == 'game_won':
        image = load_image('game_won.png')
        position_art = image.get_rect()
        pygame.mixer.music.load('data/music/game_won_music.wav')
        game_time_str = f'{game_time // 60}:{game_time % 60:0>2}'
        if music_on:
            game_sound = pygame.mixer.Sound("data/music/game_won_sound.wav")
        if progress[level_completed[keys] - 1] == '∞' or \
                datetime.strptime(game_time_str, '%M:%S') < datetime.strptime(progress[level_completed[keys] - 1], '%M:%S'):
            progress[level_completed[keys] - 1] = game_time_str
            save()
    # Экран поражения
    elif game_position == 'game_over':
        image = load_image('game_over.png')
        position_art = image.get_rect()
        pygame.mixer.music.load('data/music/game_over_music.wav')
        if music_on:
            game_sound = pygame.mixer.Sound("data/music/game_over_sound.mp3")

    if music_on:
        pygame.mixer.Sound.play(game_sound)
    running = True
    music_is_run = not music_on
    timer = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_RETURN, pygame.MOUSEBUTTONDOWN]:
                    if door and game_position == 'game_won':
                        music_on = music_is_run
                    pygame.mixer.music.stop()
                    return 1
                elif event.key == pygame.K_k:
                    pygame.mixer.music.stop() if music_on else pygame.mixer.music.play()
                    music_on = not music_on
                elif event.key == pygame.K_r:
                    pygame.mixer.music.stop()
                    return _map
        # отрисовка экрана исходя из позиции игры
        screen.fill(pygame.Color(0, 0, 0))
        screen.blit(image, position_art)
        # отрисовка времени игры
        if game_position == 'game_won' and not door:
            font = pygame.font.SysFont("Comic Sans MS", 30)
            text = font.render(f'Время прохождения - {game_time // 60}:{game_time % 60:0>2}', True, 'white')
            screen.blit(text, (55, 400))
        pygame.display.update()
        if not music_is_run and (not door or game_position == 'game_over'):
            sleep(0.9 if game_position == 'game_won' else 1.5)
            pygame.mixer.music.play(-1)
            music_is_run = True
        if door and game_position == 'game_won':
            if music_on and not music_is_run:
                music_is_run = True
                pygame.mixer.music.load("data/music/final_music.wav")
                pygame.mixer.Sound.play(final_sound)
            if game_position == 'game_won' and timer == cast_count * 1600:
                if cast_count != 4:
                    cast_count += 1
                image = load_image(f'cast_scene{cast_count}.png')
                if cast_count == 3 and music_on:
                    pygame.mixer.music.play(-1)
                    music_on = False
                elif cast_count == 3 and not music_on:
                    music_is_run = False
                position_art = image.get_rect()
                timer = 0
            timer += 1
    pygame.mixer.music.stop()
    return 0


def check_for_winner_mini_game(field):
    curplayer = list(field.keys())[0]
    solution = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 4, 7], [2, 5, 8], [3, 6, 9], [1, 5, 9], [3, 5, 7]]
    for i in solution:
        if all(j in field[curplayer] for j in i):
            return 'game_on' if curplayer == 'x' else 'game_over'
    return 'mini_game'


def mini_game(board, screen, game_position):
    global music_on
    # настройки мини-игры
    board_mg = [['', '', ''], ['', '', ''], ['', '', '']]
    pygame.mixer.music.set_volume(0.5)
    running = True
    while game_position == 'mini_game':
        board.fall = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    event_pos = event.pos
                    if 31 < event_pos[0] < 300 and 104 < event_pos[1] < 373:
                        square = ((event_pos[0] - 31) // 91, (event_pos[1] - 104) // 91)
                        if not len(board_mg[square[1]][square[0]]):
                            board_mg[square[1]][square[0]] = 'x'
                        game_position = check_for_winner_mini_game({'x': [y*3+x+1 for x in range(3) for y in range(3)
                                                                          if board_mg[y][x] == 'x']})

                        if game_position == 'mini_game':
                            chc = []
                            for y in range(3):
                                for x in range(3):
                                    if board_mg[y][x] == '':
                                        chc.append((y, x))
                            if len(chc):
                                square = choice(chc)
                                board_mg[square[0]][square[1]] = 'o'
                            game_position = check_for_winner_mini_game({'o': [y * 3 + x + 1 for x in range(3)
                                                                              for y in range(3)
                                                                              if board_mg[y][x] == 'o']})
                            if not len(chc) or game_position == 'game_over':
                                game_position = 'game_over'
                                running = False
                        else:
                            board_mg = [['', '', ''], ['', '', ''], ['', '', '']]
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                pygame.mixer.music.stop() if music_on else pygame.mixer.music.play(-1)
                music_on = not music_on
        screen.fill(pygame.Color(0, 0, 0))
        image = load_image('mini_game1.png')
        mgame_art = image.get_rect()
        screen.blit(image, mgame_art)
        for y in range(3):
            for elem in range(3):
                if board_mg[y][elem] == 'x':
                    pygame.draw.line(screen, pygame.Color("Black"), (35 + 89 * elem + 10, 108 + 89 * y + 10),
                                     (118 + 89 * elem - 10, 193 + 89 * y - 10), 7)
                    pygame.draw.line(screen, pygame.Color("Black"), (118 + 89 * elem - 10, 108 + 89 * y + 10),
                                     (35 + 89 * elem + 10, 193 + 89 * y - 10), 7)
                elif board_mg[y][elem] == 'o':
                    pygame.draw.circle(screen, pygame.Color(128, 128, 128), (77 + 89 * elem, 150 + 89 * y), 32, 6)
        pygame.display.flip()
    pygame.mixer.music.set_volume(1)
    return board, screen, game_position, running


def menu():
    global music_on
    global keys
    global door
    global con
    global cur
    global progress
    global opened_levels
    # Инициализация данных / progress.wsdb
    try:
        f = open('data/levels/progress.wsdb', mode='r')
        con = sqlite3.connect('data/levels/progress.wsdb')
        cur = con.cursor()
    except Exception:
        f = open('data/levels/progress.wsdb', mode='w')
        con = sqlite3.connect('data/levels/progress.wsdb')
        cur = con.cursor()
        cur.execute("""CREATE TABLE main (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name STRING,
                level_1 STRING DEFAULT '∞',
                level_2 STRING DEFAULT '∞',
                level_3 STRING DEFAULT '∞',
                level_4 STRING DEFAULT '∞'
            )""")
        cur.execute("""INSERT INTO main (id, name) VALUES(1, 'player')""")
        con.commit()
    f.close()
    progress = list(cur.execute("""Select level_1, level_2, level_3, level_4 from main""").fetchone())
    opened_levels = [i + 1 if i == 0 or progress[i - 1] != '∞' else 0 for i in range(4)]
    # инициализация окна
    pygame.init()
    size = 700, 400
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('The Walls')
    image = load_image('start.bmp')
    lst_of_track = os.listdir('data/music/main music')
    running_track = -1
    menu_art = image.get_rect()
    image_1 = load_image('locked_level.png')
    button_up = Button(13, 432, 84, 50)
    button_down = Button(152, 432, 84, 50)
    running = False
    # работа с пользователем
    selection = 0
    position, helping = 'menu', 1
    door = ''
    # параметры для затемнения окна
    closed = False
    opening = True
    darken_percent = 0.99
    dark = pygame.Surface((700, 500)).convert_alpha()
    while running or not closed:
        for event in pygame.event.get():
            if running:
                if position == 'menu':
                    if event.type == pygame.QUIT:
                        running = False
                        closed = True
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            event_pos = event.pos
                            keys, selection = 0, 0
                            e = event_pos[1]
                            level = [n for i, j, n in
                                     [(3, 87, 1), (93, 175, 2), (181, 262, 3), (268, 351, 4), (e, e + 1, None)] if
                                     e in range(i, j)][0]
                            if 1 < event_pos[0] < 142 and level in opened_levels:
                                keys = eval(f'keys_{level}')
                                selection = eval(f'level_{level}')
                                running = False
                                if level == 4:
                                    door = 'door(exit).png'
                            elif 553 < event_pos[0] < 694 and 2 < event_pos[1] < 87:
                                progress = ['∞'] * 4
                                save()
                                return 1
                            elif 549 < event_pos[0] < 690 and 310 < event_pos[1] < 393:
                                position, helping = 'help', 1
                                screen = pygame.display.set_mode((500, 500))

                    elif event.type == pygame.KEYDOWN:
                        pygame_keys = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4,
                                       pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3, pygame.K_KP4: 4}
                        if event.key in pygame_keys and pygame_keys[event.key] in opened_levels:
                            keys = eval(f'keys_{pygame_keys[event.key]}')
                            selection = eval(f'level_{pygame_keys[event.key]}')
                            running = False
                            if pygame_keys[event.key] == 4:
                                door = 'door(exit).png'
                        elif event.key == pygame.K_k:
                            pygame.mixer.music.stop() if music_on else pygame.mixer.music.play()
                            music_on = not music_on


                elif position == 'help':
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            event_pos = event.pos
                            if button_up.intersection(event_pos):
                                helping = button_up.next(-1, helping)
                            elif button_down.intersection(event_pos):
                                helping = button_down.next(1, helping)
                            elif 4 < event_pos[0] < 85 and 10 < event_pos[1] < 84:
                                position = 'menu'
                                screen = pygame.display.set_mode(size)

                else:
                    terminate()
        screen.fill(pygame.Color(0, 0, 0))
        if position == 'menu':
            # отрисовка меню
            screen.blit(image, menu_art)
            for lev in locked_levels:
                if int(lev) not in opened_levels:
                    screen.blit(image_1, (1, locked_levels[lev]))
        elif position == 'help':
            # отрисовка Помощи
            image2 = load_image(f"help_{helping}.png")
            help_art = image2.get_rect()
            screen.blit(image2, help_art)
            if helping == 4:
                n = 0
                time_not = [156, 179, 203, 226]
                for i in progress:
                    font = pygame.font.SysFont("Courier New", 36 if i == '∞' else 20, bold=True)
                    text = font.render(i, True, 'black')
                    screen.blit(text, (189, time_not[n] if i == '∞' else 164 + n * 23))
                    n += 1
        # затемнение окна
        if not running:
            darken_percent = round(darken_percent - 0.01, 2) if opening else round(darken_percent + 0.01, 2)
            dark.fill((0, 0, 0, darken_percent * 255))
            screen.blit(dark, (0, 0))
            if music_on:
                pygame.mixer.music.set_volume(1 - darken_percent)
            if darken_percent == 1:
                closed = True
            elif darken_percent == 0:
                running = True
                opening = False
        if music_on and not pygame.mixer.music.get_busy():
            running_track = (running_track + 1) % len(lst_of_track)
            pygame.mixer.music.load('data/music/main music/' + lst_of_track[running_track])
            pygame.mixer.music.play()
        pygame.display.update()
        clock.tick(50)
    pygame.mixer.music.stop()
    return selection


if __name__ == '__main__':
    global all_sprites
    global tiles
    global player
    _r = 1
    not_is_exit = ('', 10)
    music_on = True
    game_time = 0
    schedule.every().second.do(game_timer)
    while _r:
        all_sprites = pygame.sprite.Group()
        tiles = pygame.sprite.Group()
        player = pygame.sprite.Group()
        keys_counter = pygame.sprite.Group()
        if isinstance(_r, int):
            _r = menu()
            _map = _r
        if not isinstance(_r, int):
            camera = Camera()
            _r = game(500, 500)
