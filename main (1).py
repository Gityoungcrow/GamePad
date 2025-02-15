import sys
import sqlite3
import random
import subprocess

import pygame
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QMessageBox
from PyQt6 import QtCore, QtGui, QtWidgets
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


# class PingPongGame(QDialog):
#     def __init__(self):
#         super().__init__()
#         super(PingPongGame, self).__init__()
#         loadUi('pingpong.ui', self)


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('gamepad.ui', self)  # Загружаем дизайн

        self.pushButton.clicked.connect(self.snakegame)
        # self.pushButton_2.clicked.connect(self.tetrisgame)
        # self.pushButton_3.clicked.connect(self.pingponggame)


    def snakegame(self):
        mood_page = SnakeGame()
        mood_page.exec()


    # def snakegame(self):
    #     mood_page = SnakeGame()
    #     mood_page.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec())