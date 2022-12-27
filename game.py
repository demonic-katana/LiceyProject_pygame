import os
import sys
import pygame


class Board():
    def __init__(self, WIDTH, HEIGHT):
        self.cell = [[0] * WIDTH for i in range(HEIGHT)]


def game(WIDTH, HEIGHT):
    # инициализация окна
    pygame.init()
    size = WIDTH, HEIGHT
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    # инициализация объектов
    board = Board(10, 10)

    # игровой цикл / игра началась
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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
