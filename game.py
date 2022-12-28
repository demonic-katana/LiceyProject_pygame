import os
import sys
import pygame


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
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
_map = list(map(str.strip, open('map.txt', mode='r', encoding='utf8').readlines()))
all_sprites = pygame.sprite.Group()
tiles = pygame.sprite.Group()
player = pygame.sprite.Group()


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, image, side, sign):
        super().__init__(tiles, all_sprites)
        self.sign = sign
        self.image = image
        self.side = side
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

    def move(self, x, y):
        self.pos = (self.pos[0] + x, self.pos[1] + y)
        self.rect = self.image.get_rect().move(
            self.side * self.pos[0] + 15, self.side * self.pos[1] + 5)


class Board():
    def __init__(self, WIDTH, HEIGHT, side, map):
        self.cell = [[0] * HEIGHT for i in range(WIDTH)]
        self.borders = ['#']
        # механизм добавки ячеек, через которые нельзя проходить / пока нету /
        self.images = {
            '#': load_image('box.png'),
            '.': load_image('grass.png'),
            'p': load_image('mar.png')}
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if map[y][x] == '.':
                    self.cell[x][y] = Tile('empty', x, y, self.images['.'], side, '.')
                elif map[y][x] == '#':
                    self.cell[x][y] = Tile('wall', x, y, self.images['#'], side, '#')
                elif map[y][x] == 'p':
                    self.cell[x][y] = Tile('empty', x, y, self.images['.'], side, '.')
                    self.player = Player(x, y, self.images['p'], side)

    def move(self, x, y):
        pos = self.player.pos
        if not self.cell[pos[0] + x][pos[1] + y].process(self.borders):
            self.player.move(x, y)

    def update(self, pos):
        pass
        # функция - возможная реализация смены кадра
        # dx, dy =
        # if pos[0] // 10 > 0:


def terminate():
    pygame.quit()
    sys.exit()


def game(WIDTH, HEIGHT):
    # инициализация окна
    pygame.init()
    size = WIDTH, HEIGHT
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    # инициализация объектов
    board = Board(len(_map), len(_map[0]), 50, _map)
    # игровой цикл / игра началась
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    board.move(0, -1)
                elif event.key == pygame.K_DOWN:
                    board.move(0, 1)
                elif event.key == pygame.K_LEFT:
                    board.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    board.move(1, 0)
        screen.fill(pygame.Color(0, 0, 0))

        # отрисовка карты
        tiles.update(board.player.pos)
        tiles.draw(screen)
        # отрисовка персонажа
        player.draw(screen)

        pygame.display.flip()
    return 0


def menu():
    # заставка
    # работа с пользователем
    selection = 1
    return selection


if __name__ == '__main__':
    if menu():
        _r = game(500, 500)
        print(_r)
        sys.exit(_r)
