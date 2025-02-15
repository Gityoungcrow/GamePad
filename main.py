import sys
import sqlite3
import random

from collections import OrderedDict
from pygame import Rect
import numpy as np

import pygame
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt6.uic import loadUi


class SnakeGame(QDialog):
    def __init__(self):
        super().__init__()
        super(SnakeGame, self).__init__()
        loadUi('snake.ui', self)

        class Settings:
            SCREEN_WIDTH = 800
            SCREEN_HEIGHT = 600
            BLACK = (0, 0, 0)
            WHITE = (255, 255, 255)
            GREEN = (0, 255, 0)
            RED = (255, 0, 0)
            BLUE = (0, 0, 255)
            PINK = (255, 192, 203)
            DARK_GREEN = (0, 100, 0)
            GREY = (128, 128, 128)
            BLOCK_SIZE = 20
            SNAKE_SPEED = 15
            SPEED_DECREASE_AMOUNT = 2
            SPEED_DECREASE_DURATION = 150
            SPEED_BOOST_AMOUNT = 2
            FONT_STYLE_NAME = "bahnschrift"  # Имя шрифта, а не объект
            SCORE_FONT_NAME = "comicsansms"  # Имя шрифта, а не объект
            BEST_SCORE_FONT_NAME = "comicsansms"  # Имя шрифта, а не объект
            FONT_SIZE = 25
            SCORE_FONT_SIZE = 35
            BEST_SCORE_FONT_SIZE = 20
            DATABASE_NAME = "snake_scores.db"  # name of the database
            TABLE_NAME = "scores"  # table inside the database

        # Инициализация Pygame
        pygame.init()

        # Initialize Pygame font module AFTER pygame.init()
        pygame.font.init()

        # Создаем шрифты после инициализации
        FONT_STYLE = pygame.font.SysFont(Settings.FONT_STYLE_NAME, Settings.FONT_SIZE)
        SCORE_FONT = pygame.font.SysFont(Settings.SCORE_FONT_NAME, Settings.SCORE_FONT_SIZE)
        BEST_SCORE_FONT = pygame.font.SysFont(Settings.BEST_SCORE_FONT_NAME, Settings.BEST_SCORE_FONT_SIZE)

        # Размеры экрана
        screen = pygame.display.set_mode((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))
        pygame.display.set_caption("Змейка")

        # Класс для змейки
        class Snake:
            def __init__(self, block_size):
                self.block_size = block_size
                self.x = Settings.SCREEN_WIDTH / 2
                self.y = Settings.SCREEN_HEIGHT / 2
                self.x_change = 0
                self.y_change = 0
                self.snake_list = []
                self.length = 1
                self.head = []  # изначально не было, я добавил, чтобы правильно отрисовывать голову

            def move(self):
                self.x += self.x_change
                self.y += self.y_change

            def update(self):
                self.head = [self.x, self.y]
                self.snake_list.append(self.head)

                if len(self.snake_list) > self.length:
                    del self.snake_list[0]

            def draw(self):
                for i, x in enumerate(self.snake_list):
                    if i == len(self.snake_list) - 1:  # Голова змейки
                        pygame.draw.rect(screen, Settings.DARK_GREEN, [x[0], x[1], self.block_size, self.block_size])
                    else:
                        pygame.draw.rect(screen, Settings.GREEN, [x[0], x[1], self.block_size, self.block_size])

            def reset(self):
                self.x = Settings.SCREEN_WIDTH / 2
                self.y = Settings.SCREEN_HEIGHT / 2
                self.x_change = 0
                self.y_change = 0
                self.snake_list = []
                self.length = 1

            def collides_with(self, x, y):
                for segment in self.snake_list:
                    if segment[0] == x and segment[1] == y:
                        return True
                return False

        # Класс для еды
        class Food:
            def __init__(self, block_size, color):
                self.block_size = block_size
                self.x = 0  # Инициализируем x и y
                self.y = 0
                self.color = color
                self.generate(None, [])  # Вызываем generate при инициализации, чтобы установить начальные координаты.

            def generate(self, snake, obstacles):
                while True:
                    self.x = round(random.randrange(0,
                                                    Settings.SCREEN_WIDTH - self.block_size) / self.block_size) * self.block_size
                    self.y = round(random.randrange(0,
                                                    Settings.SCREEN_HEIGHT - self.block_size) / self.block_size) * self.block_size

                    # Проверяем, не находится ли еда на змейке или препятствиях
                    if not (snake and snake.collides_with(self.x, self.y)) and not any(
                            obstacle.x == self.x and obstacle.y == self.y for obstacle in obstacles):
                        break

            def draw(self):
                pygame.draw.rect(screen, self.color, [self.x, self.y, self.block_size, self.block_size])

        # Класс для препятствий
        class Obstacle:
            def __init__(self, block_size):
                self.block_size = block_size
                self.x = round(random.randrange(0, Settings.SCREEN_WIDTH - block_size) / block_size) * block_size
                self.y = round(random.randrange(0, Settings.SCREEN_HEIGHT - block_size) / block_size) * block_size

            def draw(self):
                pygame.draw.rect(screen, Settings.GREY, [self.x, self.y, self.block_size, self.block_size])

            def generate(self):
                self.x = round(
                    random.randrange(0, Settings.SCREEN_WIDTH - self.block_size) / self.block_size) * self.block_size
                self.y = round(
                    random.randrange(0, Settings.SCREEN_HEIGHT - self.block_size) / self.block_size) * self.block_size

        class Button:
            def __init__(self, color, x, y, width, height, text, outline=None):
                self.color = color
                self.x = x
                self.y = y
                self.width = width
                self.height = height
                self.text = text
                self.outline = outline
                self.rect = pygame.Rect(x, y, width, height)  # Храним rect для проверки кликов

            def draw(self, screen):
                if self.outline:
                    pygame.draw.rect(screen, self.outline, (self.x - 2, self.y - 2, self.width + 4, self.height + 4), 0)
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0)

                if self.text:
                    font = pygame.font.SysFont("comicsansms", 20)
                    text_surface = font.render(self.text, True, Settings.BLACK)
                    text_rect = text_surface.get_rect()  # <--- Get the rect *after* rendering
                    text_rect.center = (self.x + (self.width // 2), self.y + (self.height // 2))  # Center the rect
                    screen.blit(text_surface, text_rect)

            def is_clicked(self, pos):
                return self.rect.collidepoint(pos)

        # --- Database functions ---

        def create_table():
            """Creates the table if it doesn't exist."""
            conn = sqlite3.connect(Settings.DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {Settings.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    score INTEGER NOT NULL
                )
            """)
            conn.commit()
            conn.close()

        def get_best_score():
            """Retrieves the best score from the database."""
            conn = sqlite3.connect(Settings.DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX(score) FROM {Settings.TABLE_NAME}")
            result = cursor.fetchone()
            conn.close()
            if result and result[0] is not None:
                return result[0]
            else:
                return 0

        def save_score(score):
            """Saves the given score to the database."""
            conn = sqlite3.connect(Settings.DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {Settings.TABLE_NAME} (score) VALUES (?)", (score,))
            conn.commit()
            conn.close()

        # --- Game functions ---
        # Функция для отображения очков
        def show_score(score):
            value = SCORE_FONT.render("Очки: " + str(score), True, Settings.WHITE)
            screen.blit(value, [0, 0])

        # Функция для отображения лучшего результата
        def show_best_score():
            best_score = get_best_score()
            value = BEST_SCORE_FONT.render("Best Score: " + str(best_score), True, Settings.WHITE)
            screen.blit(value, [0, Settings.SCREEN_HEIGHT - 25])  # Размещаем внизу экрана

        # Функция для отрисовки текста
        def message(msg, color, x, y):
            mesg = FONT_STYLE.render(msg, True, color)
            screen.blit(mesg, [x, y])

        # Функция для основного игрового цикла
        def game_loop(level):
            game_over = False
            game_close = False

            snake = Snake(Settings.BLOCK_SIZE)

            # Создаем еду разных типов
            food_green = Food(Settings.BLOCK_SIZE, Settings.GREEN)
            food_blue = Food(Settings.BLOCK_SIZE, Settings.BLUE)
            food_pink = Food(Settings.BLOCK_SIZE, Settings.PINK)
            food_red = Food(Settings.BLOCK_SIZE, Settings.RED)

            # Количество препятствий в зависимости от уровня
            num_obstacles = level * 2
            obstacles = [Obstacle(Settings.BLOCK_SIZE) for _ in range(num_obstacles)]

            # Генерируем еду в первый раз
            food_green.generate(snake, obstacles)
            food_blue.generate(snake, obstacles)
            food_pink.generate(snake, obstacles)
            food_red.generate(snake, obstacles)

            score = 0

            # Настройка скорости змейки в зависимости от уровня
            current_speed = Settings.SNAKE_SPEED + (level - 1) * 5  # Увеличиваем скорость
            base_speed = current_speed  # Сохраняем базовую скорость для восстановления

            # Переменные для эффектов скорости
            slowed_down = False
            speed_boosted = False

            # Таймер для эффекта скорости
            SPEED_EFFECT_EVENT = pygame.USEREVENT + 1
            speed_effect = None

            clock = pygame.time.Clock()

            while not game_over:

                while game_close == True:
                    screen.fill(Settings.BLACK)
                    message("Вы проиграли! Нажмите C-Играть снова или Q-Выйти", Settings.RED, Settings.SCREEN_WIDTH / 6,
                            Settings.SCREEN_HEIGHT / 3)
                    show_score(score)
                    pygame.display.update()

                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_q:
                                game_over = True
                                game_close = False
                            if event.key == pygame.K_c:
                                game_loop(level)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        game_over = True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            snake.x_change = -Settings.BLOCK_SIZE
                            snake.y_change = 0
                        elif event.key == pygame.K_RIGHT:
                            snake.x_change = Settings.BLOCK_SIZE
                            snake.y_change = 0
                        elif event.key == pygame.K_UP:
                            snake.y_change = -Settings.BLOCK_SIZE
                            snake.x_change = 0
                        elif event.key == pygame.K_DOWN:
                            snake.y_change = Settings.BLOCK_SIZE
                            snake.x_change = 0
                    if event.type == SPEED_EFFECT_EVENT:
                        current_speed = base_speed
                        pygame.time.set_timer(SPEED_EFFECT_EVENT, 0)  # Disable timer
                        speed_effect = None

                if snake.x >= Settings.SCREEN_WIDTH or snake.x < 0 or snake.y >= Settings.SCREEN_HEIGHT or snake.y < 0:
                    game_close = True
                snake.move()
                snake.update()

                screen.fill(Settings.BLACK)
                food_green.draw()
                food_blue.draw()
                food_pink.draw()
                food_red.draw()

                for obstacle in obstacles:
                    obstacle.draw()

                snake.draw()

                show_score(score)
                pygame.display.update()

                # Проверка столкновения с едой
                if snake.x == food_green.x and snake.y == food_green.y:
                    food_green.generate(snake, obstacles)
                    snake.length += 1
                    score += 1  # Только зеленая еда дает очки
                elif snake.x == food_blue.x and snake.y == food_blue.y:
                    food_blue.generate(snake, obstacles)
                    if snake.length > 1:
                        snake.length -= 1
                    else:
                        game_close = True
                    score = max(0, score - 1)  # Синяя еда убавляет очки всегда
                elif snake.x == food_pink.x and snake.y == food_pink.y:
                    food_pink.generate(snake, obstacles)
                    if speed_effect is None:  # Применяем эффект, только если нет другого активного
                        current_speed = max(5, current_speed - Settings.SPEED_DECREASE_AMOUNT)
                        pygame.time.set_timer(SPEED_EFFECT_EVENT,
                                              Settings.SPEED_DECREASE_DURATION)  # Duration in milliseconds
                        speed_effect = "slow"  # сохраняем какой эффект произошел

                elif snake.x == food_red.x and snake.y == food_red.y:
                    food_red.generate(snake, obstacles)
                    if speed_effect is None:  # Применяем эффект, только если нет другого активного
                        current_speed += Settings.SPEED_BOOST_AMOUNT
                        pygame.time.set_timer(SPEED_EFFECT_EVENT,
                                              Settings.SPEED_DECREASE_DURATION)  # Duration in milliseconds
                        speed_effect = "fast"  # сохраняем какой эффект произошел

                # Проверка столкновения с собой
                for x in snake.snake_list[:-1]:
                    if x == snake.head:
                        game_close = True

                # Проверка столкновения с препятствиями
                for obstacle in obstacles:
                    if snake.x == obstacle.x and snake.y == obstacle.y:
                        game_close = True

                clock.tick(current_speed)

            snake.reset()
            return game_over, score

        # Функция для главного меню
        def game_menu():
            intro = True
            start_button = Button(Settings.GREEN, Settings.SCREEN_WIDTH / 2 - 75, Settings.SCREEN_HEIGHT / 2 + 50, 150,
                                  50, "START PLAY", Settings.BLACK)
            back_button = Button(Settings.RED, Settings.SCREEN_WIDTH / 2 - 50, Settings.SCREEN_HEIGHT / 2 + 120, 100,
                                 40, "BACK", Settings.BLACK)

            while intro:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if start_button.is_clicked(event.pos):
                            select_level()
                        elif back_button.is_clicked(event.pos):
                            pygame.quit()
                            quit()

                screen.fill(Settings.BLACK)
                message("Добро пожаловать в игру Змейка", Settings.GREEN, Settings.SCREEN_WIDTH / 6,
                        Settings.SCREEN_HEIGHT / 4)
                message("Используйте стрелки для движения", Settings.WHITE, Settings.SCREEN_WIDTH / 6,
                        Settings.SCREEN_HEIGHT / 2)
                message("Кушайте, чтобы расти!", Settings.WHITE, Settings.SCREEN_WIDTH / 6, Settings.SCREEN_HEIGHT / 3)
                show_best_score()

                start_button.draw(screen)
                back_button.draw(screen)

                pygame.display.update()

        # Функция для выбора уровня
        def select_level():
            level_select = True
            level1_button = Button(Settings.BLUE, Settings.SCREEN_WIDTH / 2 - 50, Settings.SCREEN_HEIGHT / 2, 100, 40,
                                   "Уровень 1", Settings.BLACK)
            level2_button = Button(Settings.BLUE, Settings.SCREEN_WIDTH / 2 - 50, Settings.SCREEN_HEIGHT / 2 + 50, 100,
                                   40, "Уровень 2", Settings.BLACK)
            level3_button = Button(Settings.BLUE, Settings.SCREEN_WIDTH / 2 - 50, Settings.SCREEN_HEIGHT / 2 + 100, 100,
                                   40, "Уровень 3", Settings.BLACK)
            back_button = Button(Settings.RED, Settings.SCREEN_WIDTH / 2 - 50, Settings.SCREEN_HEIGHT / 2 + 150, 100,
                                 40, "BACK", Settings.BLACK)

            while level_select:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if level1_button.is_clicked(event.pos):
                            level_select = False
                            game_over, score = game_loop(1)  # Получаем очки после игры
                            if game_over:
                                save_score(score)
                                game_menu()  # Возвращаемся в меню
                        elif level2_button.is_clicked(event.pos):
                            level_select = False
                            game_over, score = game_loop(2)
                            if game_over:
                                save_score(score)
                                game_menu()
                        elif level3_button.is_clicked(event.pos):
                            level_select = False
                            game_over, score = game_loop(3)
                            if game_over:
                                save_score(score)
                                game_menu()
                        elif back_button.is_clicked(event.pos):
                            level_select = False
                            game_menu()

                screen.fill(Settings.BLACK)
                message("Выберите уровень:", Settings.WHITE, Settings.SCREEN_WIDTH / 3, Settings.SCREEN_HEIGHT / 4)

                level1_button.draw(screen)
                level2_button.draw(screen)
                level3_button.draw(screen)
                back_button.draw(screen)

                pygame.display.update()

        # --- Main ---
        if __name__ == "__main__":
            create_table()  # Создаем таблицу при запуске игры, если ее нет
            game_menu()  # Запускаем главное меню
            pygame.quit()
            quit()


class TetrisGame(QDialog):
    def __init__(self):
        super().__init__()
        super(TetrisGame, self).__init__()
        loadUi('tetris.ui', self)

        WINDOW_WIDTH, WINDOW_HEIGHT = 500, 600
        GRID_WIDTH, GRID_HEIGHT = 300, 600
        TILE_SIZE = 30

        # Цвета
        BG_COLOR = (240, 240, 240)  # Светлый фон
        GRID_COLOR = (200, 200, 200)  # Цвет сетки
        TEXT_COLOR = (50, 50, 50)  # Цвет текста
        BLOCK_COLORS = [
            (215, 133, 133),  # Красный
            (30, 145, 255),  # Синий
            (0, 170, 0),  # Зеленый
            (180, 0, 140),  # Фиолетовый
            (200, 200, 0),  # Желтый
            (200, 200, 200)  # Серый
        ]

        # Шрифты
        pygame.font.init()
        FONT = pygame.font.Font(None, 24)  # Основной шрифт

        def remove_empty_columns(arr, _x_offset=0, _keep_counting=True):
            """Удаляет пустые колонки из массива."""
            for colid, col in enumerate(arr.T):
                if col.max() == 0:
                    if _keep_counting:
                        _x_offset += 1
                    arr, _x_offset = remove_empty_columns(
                        np.delete(arr, colid, 1), _x_offset, _keep_counting)
                    break
                else:
                    _keep_counting = False
            return arr, _x_offset

        class BottomReached(Exception):
            pass

        class TopReached(Exception):
            pass

        class Block(pygame.sprite.Sprite):

            @staticmethod
            def collide(block, group):
                """Проверяет столкновение блока с другими блоками."""
                for other_block in group:
                    if block == other_block:
                        continue
                    if pygame.sprite.collide_mask(block, other_block) is not None:
                        return True
                return False

            def __init__(self):
                super().__init__()
                self.color = random.choice(BLOCK_COLORS)
                self.current = True
                self.struct = np.array(self.struct)
                if random.randint(0, 1):
                    self.struct = np.rot90(self.struct)
                if random.randint(0, 1):
                    self.struct = np.flip(self.struct, 0)
                self._draw()

            def _draw(self, x=4, y=0):
                width = len(self.struct[0]) * TILE_SIZE
                height = len(self.struct) * TILE_SIZE
                self.image = pygame.surface.Surface([width, height])
                self.image.set_colorkey((0, 0, 0))
                self.rect = Rect(0, 0, width, height)
                self.x = x
                self.y = y
                for y, row in enumerate(self.struct):
                    for x, col in enumerate(row):
                        if col:
                            pygame.draw.rect(
                                self.image,
                                self.color,
                                Rect(x * TILE_SIZE + 1, y * TILE_SIZE + 1,
                                     TILE_SIZE - 2, TILE_SIZE - 2)
                            )
                self._create_mask()

            def redraw(self):
                self._draw(self.x, self.y)

            def _create_mask(self):
                self.mask = pygame.mask.from_surface(self.image)

            @property
            def group(self):
                return self.groups()[0]

            @property
            def x(self):
                return self._x

            @x.setter
            def x(self, value):
                self._x = value
                self.rect.left = value * TILE_SIZE

            @property
            def y(self):
                return self._y

            @y.setter
            def y(self, value):
                self._y = value
                self.rect.top = value * TILE_SIZE

            def move_left(self, group):
                self.x -= 1
                if self.x < 0 or Block.collide(self, group):
                    self.x += 1

            def move_right(self, group):
                self.x += 1
                if self.rect.right > GRID_WIDTH or Block.collide(self, group):
                    self.x -= 1

            def move_down(self, group):
                self.y += 1
                if self.rect.bottom > GRID_HEIGHT or Block.collide(self, group):
                    self.y -= 1
                    self.current = False
                    raise BottomReached

            def rotate(self, group):
                self.image = pygame.transform.rotate(self.image, 90)
                self.rect.width = self.image.get_width()
                self.rect.height = self.image.get_height()
                self._create_mask()
                while self.rect.right > GRID_WIDTH:
                    self.x -= 1
                while self.rect.left < 0:
                    self.x += 1
                while self.rect.bottom > GRID_HEIGHT:
                    self.y -= 1
                while True:
                    if not Block.collide(self, group):
                        break
                    self.y -= 1
                self.struct = np.rot90(self.struct)

            def update(self):
                if self.current:
                    self.move_down(self.group)

        class SquareBlock(Block):
            struct = (
                (1, 1),
                (1, 1)
            )

        class TBlock(Block):
            struct = (
                (1, 1, 1),
                (0, 1, 0)
            )

        class LineBlock(Block):
            struct = (
                (1,),
                (1,),
                (1,),
                (1,)
            )

        class LBlock(Block):
            struct = (
                (1, 1),
                (1, 0),
                (1, 0),
            )

        class ZBlock(Block):
            struct = (
                (0, 1),
                (1, 1),
                (1, 0),
            )

        class BlocksGroup(pygame.sprite.OrderedUpdates):

            @staticmethod
            def get_random_block():
                return random.choice(
                    (SquareBlock, TBlock, LineBlock, LBlock, ZBlock))()

            def __init__(self, *args, **kwargs):
                super().__init__(self, *args, **kwargs)
                self._reset_grid()
                self._ignore_next_stop = False
                self.score = 0
                self.next_block = None
                self.stop_moving_current_block()
                self._create_new_block()

            def _check_line_completion(self):
                for i, row in enumerate(self.grid[::-1]):
                    if all(row):
                        self.score += 5
                        affected_blocks = list(
                            OrderedDict.fromkeys(self.grid[-1 - i]))
                        for block, y_offset in affected_blocks:
                            block.struct = np.delete(block.struct, y_offset, 0)
                            if block.struct.any():
                                block.struct, x_offset = \
                                    remove_empty_columns(block.struct)
                                block.x += x_offset
                                block.redraw()
                            else:
                                self.remove(block)
                        for block in self:
                            if block.current:
                                continue
                            while True:
                                try:
                                    block.move_down(self)
                                except BottomReached:
                                    break
                        self.update_grid()
                        self._check_line_completion()
                        break

            def _reset_grid(self):
                self.grid = [[0 for _ in range(10)] for _ in range(20)]

            def _create_new_block(self):
                new_block = self.next_block or BlocksGroup.get_random_block()
                if Block.collide(new_block, self):
                    raise TopReached
                self.add(new_block)
                self.next_block = BlocksGroup.get_random_block()
                self.update_grid()
                self._check_line_completion()

            def update_grid(self):
                self._reset_grid()
                for block in self:
                    for y_offset, row in enumerate(block.struct):
                        for x_offset, digit in enumerate(row):
                            if digit == 0:
                                continue
                            rowid = block.y + y_offset
                            colid = block.x + x_offset
                            self.grid[rowid][colid] = (block, y_offset)

            @property
            def current_block(self):
                return self.sprites()[-1]

            def update_current_block(self):
                try:
                    self.current_block.move_down(self)
                except BottomReached:
                    self.stop_moving_current_block()
                    self._create_new_block()
                else:
                    self.update_grid()

            def move_current_block(self):
                if self._current_block_movement_heading is None:
                    return
                action = {
                    pygame.K_DOWN: self.current_block.move_down,
                    pygame.K_LEFT: self.current_block.move_left,
                    pygame.K_RIGHT: self.current_block.move_right
                }
                try:
                    action[self._current_block_movement_heading](self)
                except BottomReached:
                    self.stop_moving_current_block()
                    self._create_new_block()
                else:
                    self.update_grid()

            def start_moving_current_block(self, key):
                if self._current_block_movement_heading is not None:
                    self._ignore_next_stop = True
                self._current_block_movement_heading = key

            def stop_moving_current_block(self):
                if self._ignore_next_stop:
                    self._ignore_next_stop = False
                else:
                    self._current_block_movement_heading = None

            def rotate_current_block(self):
                if not isinstance(self.current_block, SquareBlock):
                    self.current_block.rotate(self)
                    self.update_grid()

        def draw_grid(background):
            """Рисует сетку."""
            for i in range(11):
                x = TILE_SIZE * i
                pygame.draw.line(
                    background, GRID_COLOR, (x, 0), (x, GRID_HEIGHT))
            for i in range(21):
                y = TILE_SIZE * i
                pygame.draw.line(
                    background, GRID_COLOR, (0, y), (GRID_WIDTH, y))

        def draw_centered_surface(screen, surface, y):
            screen.blit(surface, (400 - surface.get_width() // 2, y))

        def main():
            pygame.init()
            pygame.display.set_caption("Tetris")
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            run = True
            game_over = False

            # Создание фона
            background = pygame.Surface(screen.get_size())
            background.fill(BG_COLOR)
            draw_grid(background)
            background = background.convert()

            # Тексты
            next_block_text = FONT.render("Next:", True, TEXT_COLOR)
            score_msg_text = FONT.render("Score:", True, TEXT_COLOR)
            game_over_text = FONT.render("Game Over!", True, TEXT_COLOR)
            exit_text = FONT.render("Press SPACE to exit", True, TEXT_COLOR)

            # Таймеры
            EVENT_UPDATE_CURRENT_BLOCK = pygame.USEREVENT + 1
            EVENT_MOVE_CURRENT_BLOCK = pygame.USEREVENT + 2
            pygame.time.set_timer(EVENT_UPDATE_CURRENT_BLOCK, 1000)
            pygame.time.set_timer(EVENT_MOVE_CURRENT_BLOCK, 100)

            blocks = BlocksGroup()

            while run:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        run = False
                        break
                    elif event.type == pygame.KEYUP:
                        if not game_over:
                            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN):
                                blocks.stop_moving_current_block()
                            elif event.key == pygame.K_UP:
                                blocks.rotate_current_block()
                        if event.key == pygame.K_SPACE:  # Завершение игры по пробелу
                            run = False
                            break

                    if game_over:
                        continue

                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN):
                            blocks.start_moving_current_block(event.key)

                    try:
                        if event.type == EVENT_UPDATE_CURRENT_BLOCK:
                            blocks.update_current_block()
                        elif event.type == EVENT_MOVE_CURRENT_BLOCK:
                            blocks.move_current_block()
                    except TopReached:
                        game_over = True

                # Отрисовка
                screen.blit(background, (0, 0))
                blocks.draw(screen)
                draw_centered_surface(screen, next_block_text, 50)
                draw_centered_surface(screen, blocks.next_block.image, 100)
                draw_centered_surface(screen, score_msg_text, 240)
                score_text = FONT.render(str(blocks.score), True, TEXT_COLOR)
                draw_centered_surface(screen, score_text, 270)
                draw_centered_surface(screen, exit_text, 320)  # Текст о завершении игры

                if game_over:
                    draw_centered_surface(screen, game_over_text, 360)

                pygame.display.flip()

            pygame.quit()

        if __name__ == "__main__":
            main()


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('gamepad.ui', self)  # Загружаем дизайн

        self.pushButton.clicked.connect(self.snakegame)
        self.pushButton_2.clicked.connect(self.tetrisgame)


    def snakegame(self):
        snake_page = SnakeGame()
        snake_page.exec()

    def tetrisgame(self):
        tetris_page = TetrisGame()
        tetris_page.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec())