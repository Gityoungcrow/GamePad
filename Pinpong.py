import pygame
import random
import sys
import sqlite3  # Добавляем импорт sqlite3
import time     # Добавляем импорт time

# Инициализация Pygame
pygame.init()

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Размеры окна
WIDTH = 800
HEIGHT = 600

# Размеры ракеток
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 90

# Размеры мяча
BALL_SIZE = 15

# Скорость мяча (начальная)
BALL_SPEED = 5

# Скорость ракеток (начальная)
PADDLE_SPEED = 5

# Уровни сложности
levels = {
    1: {"ball_speed": 5, "paddle_speed": 5},
    2: {"ball_speed": 7, "paddle_speed": 6},
    3: {"ball_speed": 9, "paddle_speed": 7},
}

# Текущий уровень
current_level = 1

# Режимы игры
GAME_MODE_PVP = "человек vs человек"
GAME_MODE_PVC = "человек vs компьютер"
game_modes = [GAME_MODE_PVP, GAME_MODE_PVC]
current_game_mode = GAME_MODE_PVC

# Типы игры
GAME_TYPE_LIMITED = "с лимитом очков"
GAME_TYPE_INFINITE = "бесконечный пин-понг"
game_types = [GAME_TYPE_LIMITED, GAME_TYPE_INFINITE]
current_game_type = GAME_TYPE_LIMITED

# Состояния игры
GAME_STATE_MENU = "menu"
GAME_STATE_LEVEL_SELECT = "level_select"
GAME_STATE_GAME_TYPE_SELECT = "game_type_select"
GAME_STATE_PLAYING = "playing"
GAME_STATE_GAME_OVER = "game_over"
GAME_STATE_WIN = "win"
GAME_STATE_DETAILS = "details"
GAME_STATE_LEADERBOARD = "leaderboard"  # Добавляем состояние для просмотра таблицы лидеров
current_game_state = GAME_STATE_MENU

# База данных
DATABASE_NAME = "pong_scores.db"
TABLE_NAME = "infinite_pong_scores"

# Создание окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

# Шрифты
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# --- Database functions ---

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_score INTEGER NOT NULL,
            computer_score INTEGER NOT NULL,
            game_time REAL NOT NULL  -- Время в секундах
        )
    """)
    conn.commit()
    conn.close()

def save_infinite_pong_score(player_score, computer_score, game_time):
    """Saves the scores and game time to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO {TABLE_NAME} (player_score, computer_score, game_time)
        VALUES (?, ?, ?)
    """, (player_score, computer_score, game_time))
    conn.commit()
    conn.close()

def get_leaderboard_data():
    """Retrieves all data from the leaderboard table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT player_score, computer_score, game_time FROM {TABLE_NAME} ORDER BY game_time DESC LIMIT 10")  # Limit to top 10
    results = cursor.fetchall()
    conn.close()
    return results

def get_best_time():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT game_time FROM {TABLE_NAME} ORDER BY game_time DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return 0

# Функция для отрисовки текста
def draw_text(text, font_size, x, y, color=WHITE, font_name=None):
    if font_name:
        font = pygame.font.Font(font_name, font_size)
    else:
        font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def draw_multiline_text(text, x, y, color, font, max_width):  # Функция отрисовки многострочного текста
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        test_surface = font.render(test_line, True, color)
        if test_surface.get_width() <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    lines.append(" ".join(current_line))

    y_offset = 0
    for line in lines:
        text_surface = font.render(line, True, color)
        text_rect = text_surface.get_rect(topleft=(x, y + y_offset))
        screen.blit(text_surface, text_rect)
        y_offset += font.get_linesize()

# Функция для сброса мяча
def reset_ball():
    ball.x = WIDTH // 2
    ball.y = HEIGHT // 2
    ball.speed_x = random.choice([-levels[current_level]["ball_speed"], levels[current_level]["ball_speed"]])
    ball.speed_y = random.choice([-levels[current_level]["ball_speed"], levels[current_level]["ball_speed"]])

# Класс для ракеток
class Paddle(pygame.Rect):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.speed = PADDLE_SPEED

    def update(self):
        # Ограничение движения
        if self.top < 0:
            self.top = 0
        if self.bottom > HEIGHT:
            self.bottom = HEIGHT

    def move_by_mouse(self):
        mouse_y = pygame.mouse.get_pos()[1]
        self.y = mouse_y - PADDLE_HEIGHT // 2

# Класс для мяча
class Ball(pygame.Rect):
    def __init__(self, x, y, size):
        super().__init__(x - size // 2, y - size // 2, size, size)
        self.speed_x = 0
        self.speed_y = 0

# Создание ракеток и мяча
paddle1 = Paddle(10, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
paddle2 = Paddle(WIDTH - PADDLE_WIDTH - 10, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_SIZE)

# Счетчики очков и лимит очков
score1 = 0
score2 = 0
score_limit = 10

def reset_game():
    global score1, score2
    score1 = 0
    score2 = 0
    reset_ball()
    paddle1.y = HEIGHT // 2 - PADDLE_HEIGHT // 2
    paddle2.y = HEIGHT // 2 - PADDLE_HEIGHT // 2

def check_for_win():  # Функция для определения, выиграл ли человек на 3 уровне
    global current_game_state
    if current_game_mode == GAME_MODE_PVC and current_level == 3 and score1 >= score_limit:
        current_game_state = GAME_STATE_WIN

def advance_level(winner):
    global current_level, current_game_state

    if current_game_mode == GAME_MODE_PVC:
        if winner == 1:  # Если выиграл игрок (человек)
            if current_level < 3:
                current_level += 1  # Переходим на следующий уровень
            else:
                check_for_win()  # Проверяем, выиграл ли человек всю игру на 3 уровне
                return  # Если выиграл, то не нужно начинать новый раунд.
        elif winner == 2:  # Если выиграл компьютер
            if current_level > 1:
                current_level -= 1  # понижаем уровень
            else:
                # Остаемся на первом уровне, но выводим сообщение поражения
                current_game_state = GAME_STATE_GAME_OVER
                return  # Прекращаем дальнейшую обработку

    paddle1.speed = levels[current_level]["paddle_speed"]  # Обновляем скорость ракеток
    paddle2.speed = levels[current_level]["paddle_speed"]
    reset_ball()
    reset_game()

# Кнопки
class Button:
    def __init__(self, x, y, width, height, color, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
        self.action = action

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        draw_text(self.text, 30, self.rect.centerx, self.rect.centery, BLACK)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()

# Функции для обработки нажатий кнопок
def start_game():
    global current_game_state
    current_game_state = GAME_STATE_LEVEL_SELECT

def back_to_menu():
    global current_game_state
    current_game_state = GAME_STATE_MENU

def show_leaderboard():
    global current_game_state
    current_game_state = GAME_STATE_LEADERBOARD

def select_level(level):
    global current_level, current_game_state, paddle1, paddle2
    current_level = level
    # Обновляем скорость ракеток при смене уровня
    paddle1.speed = levels[current_level]["paddle_speed"]
    paddle2.speed = levels[current_level]["paddle_speed"]

    reset_ball()
    reset_game()
    current_game_state = GAME_STATE_GAME_TYPE_SELECT

def select_game_type(game_type):
    global current_game_type, current_game_state
    current_game_type = game_type
    reset_game()
    current_game_state = GAME_STATE_PLAYING

def show_details():
    global current_game_state
    current_game_state = GAME_STATE_DETAILS

def back_to_level_select():
    global current_game_state
    current_game_state = GAME_STATE_LEVEL_SELECT

# Создание кнопок
start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, GREEN, "START", start_game)
back_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, RED, "BACK", lambda: sys.exit())  # Закрыть игру
leaderboard_button = Button(WIDTH - 220, 30, 200, 50, BLUE, "ТАБЛИЦА ЛИДЕРОВ", show_leaderboard)  # Кнопка просмотра таблицы лидеров

level1_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50, BLUE, "Уровень 1", lambda: select_level(1))
level2_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 50, BLUE, "Уровень 2", lambda: select_level(2))
level3_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, BLUE, "Уровень 3", lambda: select_level(3))
back_to_menu_level_select_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 200, 200, 50, GRAY, "BACK", back_to_menu)

limited_button = Button(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 50, YELLOW, "С лимитом очков", lambda: select_game_type(GAME_TYPE_LIMITED))
infinite_button = Button(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 50, YELLOW, "Бесконечный пин-понг", lambda: select_game_type(GAME_TYPE_INFINITE))
back_to_level_button = Button(WIDTH // 2 - 150, HEIGHT // 2 + 150, 300, 50, GRAY, "BACK", back_to_level_select)
details_button = Button(WIDTH - 150, 50, 140, 30, GRAY, "Подробнее...", show_details)
back_to_menu_from_leaderboard = Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, GRAY, "BACK", back_to_menu)  # Кнопка возврата из таблицы лидеров

# Инициализация базы данных
create_table()

# Основной игровой цикл
running = True
start_time = 0  # Инициализируем время начала
game_time = 0  # Общее время игры в бесконечном режиме
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        # Обработка событий кнопок
        if current_game_state == GAME_STATE_MENU:
            start_button.handle_event(event)
            back_button.handle_event(event)
            leaderboard_button.handle_event(event)  # Draw the leaderboard button

        elif current_game_state == GAME_STATE_LEVEL_SELECT:
            level1_button.handle_event(event)
            level2_button.handle_event(event)
            level3_button.handle_event(event)
            back_to_menu_level_select_button.handle_event(event)

        elif current_game_state == GAME_STATE_GAME_TYPE_SELECT:
            limited_button.handle_event(event)
            infinite_button.handle_event(event)
            back_to_level_button.handle_event(event)

        elif current_game_state == GAME_STATE_DETAILS:
            back_to_level_button.handle_event(event)

        elif current_game_state == GAME_STATE_LEADERBOARD:
            back_to_menu_from_leaderboard.handle_event(event)  # Обрабатываем кнопку возврата из таблицы лидеров

        if current_game_state in (GAME_STATE_LEVEL_SELECT, GAME_STATE_MENU, GAME_STATE_GAME_TYPE_SELECT):
            details_button.handle_event(event)  # Details button доступна в этих состояниях

        if current_game_state == GAME_STATE_PLAYING and current_game_type == GAME_TYPE_INFINITE and event.type == pygame.KEYDOWN:
            current_game_state = GAME_STATE_MENU  # завершаем бесконечный режим
            end_time = time.time()  # фиксируем время окончания
            game_time = end_time - start_time  # общее время игры
            save_infinite_pong_score(score1, score2, game_time)  # сохраняем результат
            # Reset the timer after saving the score
            start_time = 0
            game_time = 0

    # Логика игры
    if current_game_state == GAME_STATE_PLAYING:
        # Управление ракетками
        if current_game_mode == GAME_MODE_PVP:
            # Игрок 1 управляет левой ракеткой мышью
            paddle1.move_by_mouse()

            # Игрок 2 управляет правой ракеткой мышью
            if pygame.mouse.get_pressed()[2]:  # Правая кнопка мыши
                paddle2.move_by_mouse()

        elif current_game_mode == GAME_MODE_PVC:
            # Игрок управляет левой ракеткой мышью
            paddle1.move_by_mouse()

            # Компьютерный противник
            if ball.centery < paddle2.centery and paddle2.top > 0:
                paddle2.y -= paddle2.speed
            if ball.centery > paddle2.centery and paddle2.bottom < HEIGHT:
                paddle2.y += paddle2.speed

        # Обновление положения ракеток (ограничение движения)
        paddle1.update()
        paddle2.update()

        # Движение мяча
        ball.x += ball.speed_x
        ball.y += ball.speed_y

        # Отскок от стен
        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball.speed_y = -ball.speed_y

        # Отскок от ракеток
        if ball.colliderect(paddle1) or ball.colliderect(paddle2):
            ball.speed_x = -ball.speed_x

        # Подсчет очков
        if ball.left <= 0:
            score2 += 1
            reset_ball()
        elif ball.right >= WIDTH:
            score1 += 1
            reset_ball()

        # Проверка на конец игры
        if current_game_type == GAME_TYPE_LIMITED:
            if score1 >= score_limit or score2 >= score_limit:
                winner = 1 if score1 > score2 else 2  # Определяем победителя

                if winner == 1 and current_level == 3 and current_game_mode == GAME_MODE_PVC:
                    check_for_win()
                elif winner == 2 and current_level == 1 and current_game_mode == GAME_MODE_PVC:
                    current_game_state = GAME_STATE_GAME_OVER
                else:
                    advance_level(winner)  # Меняем уровень в зависимости от победителя
        elif current_game_type == GAME_TYPE_INFINITE:
            if start_time == 0:
                start_time = time.time()  # фиксируем время начала

    # Отрисовка
    screen.fill(BLACK)

    if current_game_state == GAME_STATE_MENU:
        draw_text("PONG", 72, WIDTH // 2, HEIGHT // 4)
        start_button.draw(screen)
        back_button.draw(screen)
        leaderboard_button.draw(screen)  # Draw the leaderboard button
        best_time = get_best_time()
        draw_text(f"Лучшее время: {best_time:.1f}", 20, WIDTH // 2, HEIGHT - 30, YELLOW)  # Выводим лучшее время

    elif current_game_state == GAME_STATE_LEVEL_SELECT:
        draw_text("Выберите уровень", 48, WIDTH // 2, HEIGHT // 4)
        level1_button.draw(screen)
        level2_button.draw(screen)
        level3_button.draw(screen)
        back_to_menu_level_select_button.draw(screen)
        details_button.draw(screen)

    elif current_game_state == GAME_STATE_GAME_TYPE_SELECT:
        draw_text("Выберите режим игры", 48, WIDTH // 2, HEIGHT // 4)
        limited_button.draw(screen)
        infinite_button.draw(screen)
        back_to_level_button.draw(screen)
        details_button.draw(screen)

    elif current_game_state == GAME_STATE_PLAYING:
        pygame.draw.rect(screen, WHITE, paddle1)
        pygame.draw.rect(screen, WHITE, paddle2)
        pygame.draw.ellipse(screen, WHITE, ball)

        # Отрисовка сетки
        for i in range(0, HEIGHT, 30):
            pygame.draw.line(screen, WHITE, (WIDTH // 2, i), (WIDTH // 2, i + 15), 2)

        draw_text(str(score1), 50, WIDTH // 4, 30)
        draw_text(str(score2), 50, 3 * WIDTH // 4, 30)

        draw_text(f"Уровень: {current_level}", 30, WIDTH // 2, HEIGHT - 60)
        draw_text(current_game_mode, 30, WIDTH // 2, HEIGHT - 30)
        draw_text(current_game_type, 20, WIDTH // 2, 30, YELLOW)  # Вывод типа игры

        # Отображаем время игры, если играем в бесконечном режиме
        if current_game_type == GAME_TYPE_INFINITE:
            current_time = time.time() - start_time
            draw_text(f"Время: {current_time:.1f}", 20, WIDTH // 2, 60, YELLOW)

    elif current_game_state == GAME_STATE_WIN:
        draw_text("Вы выиграли!", 72, WIDTH // 2, HEIGHT // 2, GREEN)
        pygame.display.flip()  # Обновляем экран
        pygame.time.delay(3000)  # ждем 3 секунды
        current_game_state = GAME_STATE_MENU  # Возвращаемся в меню

    elif current_game_state == GAME_STATE_GAME_OVER:
        draw_text("Вы проиграли! Но не расстраивайся, у тебя еще много попыток)", 36, WIDTH // 2, HEIGHT // 2, RED)
        pygame.display.flip()  # Обновляем экран
        pygame.time.delay(3000)  # ждем 3 секунды
        current_game_state = GAME_STATE_MENU  # Возвращаемся в меню

    elif current_game_state == GAME_STATE_DETAILS:
        # Описания режимов игры
        details_text = {
            GAME_TYPE_LIMITED: "С лимитом очков: Вы повышаете уровни, если выигрываете, и понижаете, если проигрываете.",
            GAME_TYPE_INFINITE: "Бесконечный пин-понг: Играйте на выбранном уровне, пока не надоест. Нажмите любую клавишу, чтобы завершить."
        }
        draw_text("Описание режимов:", 48, WIDTH // 2, 50, WHITE)
        y_position = 150
        for game_type, description in details_text.items():
            draw_text(game_type, 36, WIDTH // 2, y_position, YELLOW)
            draw_multiline_text(description, 50, y_position + 50, WHITE, small_font, WIDTH - 100)
            y_position += 150
        back_to_level_button.draw(screen)  # Кнопка возврата

    elif current_game_state == GAME_STATE_LEADERBOARD:
        draw_text("ТАБЛИЦА ЛИДЕРОВ", 48, WIDTH // 2, 50)
        leaderboard_data = get_leaderboard_data()

        y_offset = 100
        draw_text("Player", 24, WIDTH // 4 - 20, y_offset + 10, YELLOW)
        draw_text("Computer", 24, WIDTH // 2 - 20, y_offset + 10, YELLOW)
        draw_text("Time", 24, 3 * WIDTH // 4 - 20, y_offset + 10, YELLOW)
        y_offset += 40

        for i, (player_score, computer_score, game_time) in enumerate(leaderboard_data):
            draw_text(str(player_score), 20, WIDTH // 4 - 20, y_offset, WHITE)
            draw_text(str(computer_score), 20, WIDTH // 2 - 20, y_offset, WHITE)
            draw_text(f"{game_time:.1f}", 20, 3 * WIDTH // 4 - 20, y_offset, WHITE)  # Форматируем время
            y_offset += 30

        back_to_menu_from_leaderboard.draw(screen)  # Отрисовываем кнопку возврата.

    pygame.display.flip()

    # FPS
    pygame.time.Clock().tick(60)

pygame.quit()