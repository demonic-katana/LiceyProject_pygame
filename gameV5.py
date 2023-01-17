import os
import sys
import pygame
from time import sleep


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


WIDTH, HEIGHT = 500, 500
keys_1, level_1 = 5, list(map(str.strip, open('data/levels/level_01.map', mode='r', encoding='utf8').readlines()))
keys_2, level_2 = 10, list(map(str.strip, open('data/levels/level_02.map', mode='r', encoding='utf8').readlines()))
keys_3, level_3 = 15, list(map(str.strip, open('data/levels/level_03.map', mode='r', encoding='utf8').readlines()))
tile_width = tile_height = 50


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, image, side, sign):
        super().__init__(tiles, all_sprites)
        self.sign = sign
        self.image = image
        self.side = side
        self.abs_pos = [pos_x, pos_y]
        self.rect = self.image.get_rect().move(
            self.side * pos_x, self.side * pos_y)

    def process(self, signs):
        return self.sign in signs


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, image, side):
        super().__init__(player, all_sprites)
        self.image = image
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
    def __init__(self, WIDTH, HEIGHT, side, map):
        self.cell = [[0] * HEIGHT for i in range(WIDTH)]
        self.borders = ['#']
        # механизм добавки ячеек, через которые нельзя проходить / пока нету /
        self.exit_pos = (0, 0)
        self.images = {
            '#': load_image('wall.png'),
            '.': load_image('floor.png'),
            'p': load_image('player.png'),
            'o': load_image('hole.png'),
            'm': load_image('key.png'),
            'e': load_image('door.png')}
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if map[y][x] == '.':
                    self.cell[x][y] = Tile('empty', x, y, self.images['.'], side, '.')
                elif map[y][x] == '#':
                    self.cell[x][y] = Tile('wall', x, y, self.images['#'], side, '#')
                elif map[y][x] == 'o':
                    self.cell[x][y] = Tile('empty', x, y, self.images['o'], side, 'o')
                elif map[y][x] == 'm':
                    self.cell[x][y] = Tile('empty', x, y, self.images['m'], side, 'm')
                elif map[y][x] == 'e':
                    self.cell[x][y] = Tile('empty', x, y, self.images['e'], side, 'e')
                    self.exit_pos = (x, y)
                elif map[y][x] == 'p':
                    self.cell[x][y] = Tile('empty', x, y, self.images['.'], side, '.')
                    self.player = Player(x, y, self.images['p'], side)
        self.WIDTH_IN_CAGES = x - 1
        self.HEIGHT_IN_CAGES = y - 1

    def move(self, x, y):
        pos = self.player.pos
        draw_pos = self.player.draw_pos
        if not self.cell[pos[0] + x][pos[1] + y].process(self.borders):
            # проверка на то, что лучше сместить: камеру или персонажа
            check_move = x or y
            check_pos = pos[0] if x else pos[1]
            check_d_pos = draw_pos[0] if x else draw_pos[1]
            max_pos = (self.WIDTH_IN_CAGES if x else self.HEIGHT_IN_CAGES) - 3
            if not (4 < check_pos < max_pos) or (check_d_pos in [4, 5] and check_d_pos + check_move in [4, 5]):
                self.player.move(x, y, 'player')
            else:
                self.player.move(x, y, 'camera')

    def update(self, pos):
        pass
        # функция - возможная реализация смены кадра
        # dx, dy =
        # if pos[0] // 10 > 0:


def terminate():
    pygame.quit()
    sys.exit()


def check_door(door_is_open, cell_is_door):
    return (not cell_is_door) or (door_is_open and cell_is_door)


def game(WIDTH, HEIGHT):
    global music_on
    # инициализация окна
    pygame.init()
    size = WIDTH, HEIGHT
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('The Walls')
    pygame.mixer.music.load('data/music/main_music.wav')
    if music_on:
        pygame.mixer.music.play(-1)
    # инициализация объектов
    board = Board(len(_map), len(_map[0]), 50, _map)
    # счётчик ключей
    players_keys = 0
    keys_color = (255, 0, 0)
    key_sound = pygame.mixer.Sound("data/music/take_key.wav")
    door_is_open = False
    door_opening_sound = pygame.mixer.Sound("data/music/opening_door.wav")
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
    running = True
    while running:
        player_pos = board.player.pos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and check_door(door_is_open,
                                                           board.cell[player_pos[0]][player_pos[1] - 1].process(['e'])):
                    board.move(0, -1)
                elif event.key == pygame.K_DOWN and check_door(door_is_open,
                                                               board.cell[player_pos[0]][player_pos[1] + 1].process(
                                                                   ['e'])):
                    board.move(0, 1)
                elif event.key == pygame.K_LEFT and check_door(door_is_open,
                                                               board.cell[player_pos[0] - 1][player_pos[1]].process(
                                                                   ['e'])):
                    board.move(-1, 0)
                elif event.key == pygame.K_RIGHT and check_door(door_is_open,
                                                                board.cell[player_pos[0] + 1][player_pos[1]].process(
                                                                    ['e'])):
                    board.move(1, 0)

                elif event.key == pygame.K_k:
                    if music_on:
                        pygame.mixer.music.stop()
                        music_on = False
                    else:
                        pygame.mixer.music.play()
                        music_on = True

                elif event.key == pygame.K_ESCAPE:
                    return 1

        player_pos = board.player.pos
        if board.cell[player_pos[0]][player_pos[1]].process(['m']):
            board.cell[player_pos[0]][player_pos[1]].image = board.images['.']
            board.cell[player_pos[0]][player_pos[1]].sign = '.'
            players_keys += 1
            if music_on:
                pygame.mixer.Sound.play(key_sound)
            if players_keys == keys:
                keys_color = (0, 255, 0)
                door_is_open = True
                if music_on:
                    pygame.mixer.Sound.play(door_opening_sound)
                board.cell[board.exit_pos[0]][board.exit_pos[1]].image = load_image('door_open.png')
        elif board.cell[player_pos[0]][player_pos[1]].process(['o']):
            running = False
            game_position = 'game_over'
        elif board.cell[player_pos[0]][player_pos[1]].process(['e']):
            running = False
            game_position = 'game_won'
        screen.fill(pygame.Color(0, 0, 0))
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
        font = pygame.font.Font(None, 25)
        text = font.render(str(players_keys), True, keys_color)
        screen.blit(text, (26, 5))
        pygame.display.flip()

    pygame.mixer.music.stop()
    if game_position == 'game_won':
        image = load_image('game_won.png')
        position_art = image.get_rect()
        pygame.mixer.music.load('data/music/game_won_music.wav')
        if music_on:
            game_sound = pygame.mixer.Sound("data/music/game_won_sound.wav")

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
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    return 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_k:
                    if music_on:
                        pygame.mixer.music.stop()
                        music_on = False
                    else:
                        pygame.mixer.music.play(-1)
                        music_on = True
        # отрисовка экрана исходя из позиции игры
        screen.fill(pygame.Color(0, 0, 0))
        screen.blit(image, position_art)
        pygame.display.update()
        if not music_is_run:
            sleep(0.9 if game_position == 'game_won' else 1.5)
            pygame.mixer.music.play(-1)
            music_is_run = True
    pygame.mixer.music.stop()
    return 0


def menu():
    global music_on
    global keys
    # инициализация окна
    pygame.init()
    size = 700, 400
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('The Walls')
    image = load_image('start.bmp')
    pygame.mixer.music.load('data/music/start_music.mp3')
    if music_on:
        pygame.mixer.music.play(-1)
    menu_art = image.get_rect()
    running = True
    # работа с пользователем
    selection = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    event_pos = event.pos
                    if 1 < event_pos[0] < 142 and 2 < event_pos[1] < 87:
                        keys = keys_1
                        selection = level_1
                        running = False
                    elif 1 < event_pos[0] < 142 and 92 < event_pos[1] < 175:
                        keys = keys_2
                        selection = level_2
                        running = False
                    elif 1 < event_pos[0] < 142 and 180 < event_pos[1] < 262:
                        keys = keys_3
                        selection = level_3
                        running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    keys = keys_1
                    selection = level_1
                    running = False
                elif event.key == pygame.K_2:
                    keys = keys_2
                    selection = level_2
                    running = False
                elif event.key == pygame.K_3:
                    keys = keys_3
                    selection = level_3
                    running = False
                elif event.key == pygame.K_k:
                    if music_on:
                        pygame.mixer.music.stop()
                        music_on = False
                    else:
                        pygame.mixer.music.play(-1)
                        music_on = True
                print(event.key)
        # отрисовка меню
        screen.fill(pygame.Color(0, 0, 0))
        screen.blit(image, menu_art)
        pygame.display.update()
    pygame.mixer.music.stop()
    return selection


if __name__ == '__main__':
    global all_sprites
    global tiles
    global player
    _r = 1
    music_on = True
    while _r == 1:
        all_sprites = pygame.sprite.Group()
        tiles = pygame.sprite.Group()
        player = pygame.sprite.Group()
        keys_counter = pygame.sprite.Group()
        _r = menu()
        _map = _r
        if _r:
            camera = Camera()
            _r = game(500, 500)
            print(_r)
