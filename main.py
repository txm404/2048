import pygame
import random
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 游戏常量
BOARD_SIZE = 4
TILE_SIZE = 100
TILE_MARGIN = 10
BOARD_WIDTH = BOARD_SIZE * (TILE_SIZE + TILE_MARGIN) + TILE_MARGIN
BOARD_HEIGHT = BOARD_WIDTH
SCORE_HEIGHT = 60 # slightly increased for style
SCREEN_WIDTH = BOARD_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT + SCORE_HEIGHT
FPS = 60

# 排行榜常量
LEADERBOARD_FILE = "leaderboard.txt"
LEADERBOARD_SIZE = 10 # 存储前10名分数

# 赛博朋克颜色定义
COLOR_BACKGROUND = (15, 22, 36)  # 深海军蓝/近乎黑色
COLOR_EMPTY_TILE = (30, 40, 55)   # 深灰色蓝调
COLOR_GRID_LINES = (10, 15, 25)   # 非常暗的背景用于网格线（如果可见）
COLOR_SCORE_BACKGROUND = (20, 28, 40) # 略浅于背景的深色
COLOR_TEXT_NEON_CYAN = (0, 255, 255) # 霓虹青色
COLOR_TEXT_NEON_MAGENTA = (255, 0, 255) # 霓虹洋红色
COLOR_TEXT_NEON_YELLOW = (255, 255, 0)  # 霓虹黄色
COLOR_TEXT_LIGHT = (220, 220, 220) # 亮灰色/白色，用于分数等
COLOR_TEXT_DARK = (180,180,180) # 用于低数值方块的浅色文字

# 赛博朋克方块颜色 (根据数字值)
TILE_COLORS = {
    0: COLOR_EMPTY_TILE,
    2: (50, 68, 92),    # 深蓝灰色
    4: (68, 89, 120),   # 蓝灰色
    8: (70, 100, 170),   # 霓虹蓝调 # (242, 177, 121) -> 赛博蓝
    16: (90, 130, 200),  # 亮霓虹蓝 # (245, 149, 99) -> 赛博青
    32: (130, 80, 180),  # 霓虹紫 # (246, 124, 95)-> 赛博紫
    64: (180, 60, 150),  # 深霓虹洋红 # (246, 94, 59) -> 赛博洋红
    128: (227, 207, 20), # 暗霓虹黄/金色 # (237, 207, 114) -> 变化不大的黄
    256: (237, 220, 40), # 亮霓虹黄 #(237, 204, 97)
    512: (237, 180, 30), # 橙黄色  #(237, 200, 80)
    1024: (255, 100, 100),# 霓虹红/粉色 #(237, 197, 63) -> 赛博红
    2048: (0, 255, 128),  # 亮霓虹绿/青色 # (237, 194, 46) -> 胜利色！
    4096: (255, 255, 255), # 超越2048，纯白/亮银 未来感 # (60, 58, 50)
}

# 字体 (我们将在 main 中尝试加载赛博朋克字体)
FONT_NAME_PRIMARY = "Consolas" # 一个常见的等宽字体，有科技感
FONT_NAME_FALLBACK = "Arial" # 如果找不到 Consolas，则使用 Arial
FONT_SIZE_LARGE = 45 # 调整了一些大小
FONT_SIZE_MEDIUM = 30
FONT_SIZE_SCORE = 35 # 分数的特定字体大小
FONT_SIZE_SMALL = 22
FONT_SIZE_MESSAGE = 55 # Game Over / You Won 消息


class Game2048:
    """
    Represents the 2048 game state and logic.
    """
    def __init__(self):
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.score = 0
        self.game_over = False
        self.won = False # Track if user reached 2048
        self.game_over_effect_timer = 0 # Timer for game over visual effect
        self.win_effect_timer = 0 # Timer for win visual effect

        self.game_state = 'MENU' # Game states: 'MENU', 'PLAYING', 'GAME_OVER', 'WON'

        self.leaderboard = [] # Initialize leaderboard list
        self.load_leaderboard() # Load scores on startup

        # Load sound effects (place your sound files in the same directory or specify path)
        self.move_sound = self.load_sound("move.wav")
        self.merge_sound = self.load_sound("merge.wav")
        self.game_over_sound = self.load_sound("game_over.wav")
        self.win_sound = self.load_sound("win.wav")

        self.init_board()

    def load_leaderboard(self):
        """
        Loads the leaderboard from the file.
        """
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                self.leaderboard = [int(line.strip()) for line in f if line.strip().isdigit()]
            self.leaderboard.sort(reverse=True) # Sort in descending order
            self.leaderboard = self.leaderboard[:LEADERBOARD_SIZE] # Keep only top scores
            logging.info(f"Leaderboard loaded: {self.leaderboard}")
        except FileNotFoundError:
            logging.info(f"Leaderboard file '{LEADERBOARD_FILE}' not found. Starting with empty leaderboard.")
            self.leaderboard = []
        except Exception as e:
            logging.error(f"Error loading leaderboard: {e}")
            self.leaderboard = [] # Reset leaderboard on error

    def save_leaderboard(self):
        """
        Saves the current score to the leaderboard if it's a high score,
        then saves the updated leaderboard to the file.
        """
        # Add current score if it's not zero and is a high score
        if self.score > 0:
            self.leaderboard.append(self.score)
            self.leaderboard.sort(reverse=True)
            self.leaderboard = self.leaderboard[:LEADERBOARD_SIZE] # Keep only top scores
            logging.info(f"Current score {self.score} added to leaderboard. New leaderboard: {self.leaderboard}")

        try:
            with open(LEADERBOARD_FILE, 'w') as f:
                for score in self.leaderboard:
                    f.write(f"{score}\n")
            logging.info(f"Leaderboard saved to '{LEADERBOARD_FILE}'.")
        except Exception as e:
            logging.error(f"Error saving leaderboard: {e}")


    def load_sound(self, filename):
        """
        Loads a sound file and returns a pygame.mixer.Sound object.
        Returns None if the file cannot be loaded.
        """
        try:
            sound = pygame.mixer.Sound(filename)
            logging.info(f"Successfully loaded sound: {filename}")
            return sound
        except pygame.error as e:
            logging.warning(f"Could not load sound file '{filename}': {e}")
            return None

    # This method should be in the Game2048 class
    def init_board(self):
        """
        Initializes the game board with two random tiles.
        """
        self.add_random_tile()
        self.add_random_tile()
        logging.info("Board initialized (Cyberpunk).")
        self.print_board() # Helper to see initial state

    # This method should be in the Game2048 class
    def add_random_tile(self):
        """
        Adds a new tile (2 or 4) to a random empty cell.
        Returns True if successful, False otherwise (no empty cells).
        """
        empty_cells = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0:
                    empty_cells.append((r, c))

        if not empty_cells:
            logging.debug("No empty cells to add a tile.")
            return False

        row, col = random.choice(empty_cells)
        # 90% chance of 2, 10% chance of 4
        self.board[row][col] = random.choice([2] * 9 + [4] * 1)
        logging.debug(f"Added {self.board[row][col]} tile at ({row}, {col})")
        return True

    # This method should be in the Game2048 class
    def can_move(self):
        """
        Checks if any moves are possible (any empty cells or adjacent same tiles).
        This is used as part of the game over check.
        """
        if any(0 in row for row in self.board):
            return True

        # Check horizontal moves
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE - 1):
                if self.board[r][c] == self.board[r][c+1]:
                    return True

        # Check vertical moves
        for c in range(BOARD_SIZE):
            for r in range(BOARD_SIZE - 1):
                if self.board[r][c] == self.board[r+1][c]:
                    return True

        logging.debug("No possible moves left.")
        return False

    # This method should be in the Game2048 class
    def is_game_over(self):
        """
        Checks if the game is over.
        Game is over if there are no empty cells and no possible moves (adjacent same tiles).
        """
        is_over = not self.can_move()
        if is_over:
            self.game_over = True
            logging.info("Game Over.")
            self.save_leaderboard() # Save leaderboard when game is over
            if self.game_over_sound: # Play game over sound
                self.game_over_sound.play()
        return is_over

    # This method should be in the Game2048 class
    def print_board(self):
        """
        Helper function to print the board state to console for debugging.
        """
        logging.debug("Current Board State:")
        for row in self.board:
            logging.debug(row)
        logging.debug("-" * (BOARD_SIZE * 6)) # Separator for easier reading

    # This method should be in the Game2048 class
    def move_left(self):
        """
        Moves tiles to the left and merges them.
        Returns True if any tiles moved or merged, False otherwise.
        """
        board_changed = False
        # new_board is not used, so it's removed.
        # new_board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        for r in range(BOARD_SIZE):
            original_row_tuple = tuple(self.board[r]) # Keep a copy for checking change

            row_values = [tile for tile in self.board[r] if tile != 0] # Remove zeros

            # Merge adjacent same tiles
            merged_row_values = []
            i = 0
            while i < len(row_values):
                if i + 1 < len(row_values) and row_values[i] == row_values[i+1]:
                    merged_value = row_values[i] * 2
                    merged_row_values.append(merged_value)
                    self.score += merged_value
                    logging.debug(f"Merged {row_values[i]} and {row_values[i+1]} to {merged_value}. Score: {self.score}")
                    if self.merge_sound: # Play merge sound
                        self.merge_sound.play()
                    # Check for win condition
                    if merged_value == 2048 and not self.won: # Check !self.won to log only once
                        self.won = True
                        logging.info("SYSTEM ALERT: Target 2048 Acquired!")
                    i += 2 # Skip the next tile as it was merged
                else:
                    merged_row_values.append(row_values[i])
                    i += 1

            # Create the new row for the board with zeros at the end
            new_row_for_board = merged_row_values + [0] * (BOARD_SIZE - len(merged_row_values))


            # Check if the row changed
            if tuple(new_row_for_board) != original_row_tuple:
                 board_changed = True
            self.board[r] = new_row_for_board # Update the row in the board


        if board_changed:
            logging.debug("Board matrix altered by move_left operation.")
            self.add_random_tile()
            self.print_board()
            if not self.can_move(): # Check for game over only if a move was made and new tile added
                 self.is_game_over()
        else:
            logging.debug("Board matrix unchanged after move_left operation.")

        return board_changed

    # This method should be in the Game2048 class
    def move(self, direction):
        """
        Handles tile movement based on the direction input.
        Rotates the board, performs left move, rotates back.
        Returns True if the board changed, False otherwise.
        """
        # Save current board state to check if any change occurred
        # original_board = [row[:] for row in self.board] # Not needed, move_left returns change

        moved = False
        if direction == 'left':
            moved = self.move_left()
        elif direction == 'right':
            self.board = self.rotate_board(self.board, 2)
            moved = self.move_left()
            self.board = self.rotate_board(self.board, 2)
        elif direction == 'up':
            self.board = self.rotate_board(self.board, 3) # Counter-clockwise for up (data moves "left" in rotated view)
            moved = self.move_left()
            self.board = self.rotate_board(self.board, 1) # Rotate back
        elif direction == 'down':
            self.board = self.rotate_board(self.board, 1) # Clockwise for down
            moved = self.move_left()
            self.board = self.rotate_board(self.board, 3) # Rotate back

        if moved and self.move_sound:
            self.move_sound.play()

        return moved


    # This method should be in the Game2048 class
    def rotate_board(self, board, times):
        """
        Rotates the board 90 degrees clockwise 'times' number of times.
        """
        temp_board = board
        for _ in range(times):
            temp_board = [list(row) for row in zip(*temp_board[::-1])] # Ensure it's a list of lists
        logging.debug(f"Rotated board matrix {times} times.")
        # self.print_board_state(temp_board) # Helper to see state after rotation
        return temp_board # Return the rotated board

    # Helper function used by rotate_board for logging only
    # This method should be in the Game2048 class
    def print_board_state(self, board_state):
         """
         Helper function to print a given board state for debugging rotations.
         """
         logging.debug("Rotated Board State:")
         for row in board_state:
             logging.debug(row)
         logging.debug("-" * (BOARD_SIZE * 6)) # Separator

    # This method should be in the Game2048 class
    def draw(self, screen, fonts):
        """
        Draws the game board, tiles, numbers, and score in Cyberpunk style.
        'fonts' is a dictionary: {'large': font_large, 'medium': font_medium, 'small': font_small, 'score': font_score, 'message': font_message}
        """
        # Draw background and grid lines for a subtle cyberpunk terminal look
        screen.fill(COLOR_BACKGROUND)

        # Draw score area with a neon accent
        pygame.draw.rect(screen, COLOR_SCORE_BACKGROUND, (0, 0, SCREEN_WIDTH, SCORE_HEIGHT))
        # Neon line accent for score area
        pygame.draw.line(screen, COLOR_TEXT_NEON_CYAN, (0, SCORE_HEIGHT - 2), (SCREEN_WIDTH, SCORE_HEIGHT - 2), 2)

        # Draw score with neon glow effect
        score_text_surface = fonts['score'].render(f"SCORE: {self.score}", True, COLOR_TEXT_NEON_YELLOW)
        score_rect = score_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCORE_HEIGHT // 2))
        # Draw glow layers
        for offset in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
             glow_surface = fonts['score'].render(f"SCORE: {self.score}", True, (COLOR_TEXT_NEON_YELLOW[0], COLOR_TEXT_NEON_YELLOW[1], COLOR_TEXT_NEON_YELLOW[2], 50)) # Semi-transparent glow color
             glow_rect = glow_surface.get_rect(center=(score_rect.centerx + offset[0], score_rect.centery + offset[1]))
             screen.blit(glow_surface, glow_rect)
        screen.blit(score_text_surface, score_rect) # Draw original text on top


        # Draw tiles with cyberpunk colors
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                tile_value = self.board[r][c]
                # Use special color for 2048, otherwise from TILE_COLORS
                if tile_value == 2048:
                    tile_color = TILE_COLORS [2048]
                elif tile_value > 2048: # for 4096 and above
                    tile_color = TILE_COLORS.get(4096, (200,200,200)) # Default bright if not defined
                else:
                    tile_color = TILE_COLORS.get(tile_value, COLOR_EMPTY_TILE)


                # Calculate tile position
                left = TILE_MARGIN + c * (TILE_SIZE + TILE_MARGIN)
                top = SCORE_HEIGHT + TILE_MARGIN + r * (TILE_SIZE + TILE_MARGIN)

                # Draw tile rectangle with a slight "glitch" or "neon glow" effect (optional, subtle border)
                pygame.draw.rect(screen, tile_color, (left, top, TILE_SIZE, TILE_SIZE), border_radius=5)
                # Add a subtle darker border to make tiles pop a bit more from the background
                pygame.draw.rect(screen, COLOR_BACKGROUND, (left, top, TILE_SIZE, TILE_SIZE), width=2, border_radius=5)


                # Draw tile number if not zero
                if tile_value != 0:
                    font_to_use = fonts['large']
                    if tile_value >= 1000: # e.g., 1024, 2048
                        font_to_use = fonts['small']
                    elif tile_value >= 100: # e.g., 128, 256, 512
                        font_to_use = fonts['medium']


                    # Determine text color based on tile value for contrast
                    if tile_value >= 8: # Brighter tiles get lighter text or a specific neon
                        text_color = COLOR_TEXT_LIGHT if tile_value < 128 else COLOR_TEXT_NEON_YELLOW # Neon for higher values
                        if tile_value == 2048:
                            text_color = COLOR_BACKGROUND # Dark text on very bright 2048_WIN_COLOR
                        elif tile_value > 2048: # For numbers like 4096
                             text_color = COLOR_BACKGROUND # Dark text on pure white
                    else: # Darker tiles (2, 4)
                        text_color = COLOR_TEXT_DARK

                    number_text_surface = font_to_use.render(str(tile_value), True, text_color)
                    number_rect = number_text_surface.get_rect(center=(left + TILE_SIZE // 2, top + TILE_SIZE // 2))
                    screen.blit(number_text_surface, number_rect)

        # Draw game over or win screen overlay
        if self.game_over or self.won:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - SCORE_HEIGHT), pygame.SRCALPHA) # Overlay for game area only

            # Simple flashing effect based on timer
            alpha = 150 + 50 * ((pygame.time.get_ticks() // 250) % 2) # Flash between 150 and 200 alpha
            overlay.fill((COLOR_BACKGROUND[0], COLOR_BACKGROUND[1], COLOR_BACKGROUND[2], alpha)) # Darker, more opaque overlay with flashing
            screen.blit(overlay, (0, SCORE_HEIGHT))

            message_text = "SYSTEM FAILURE" if self.game_over and not self.won else "OBJECTIVE COMPLETE: 2048"
            if self.won and self.game_over: # Reached 2048 but no more moves
                 message_text = "OBJECTIVE 2048 // GRIDLOCK"


            message_color = COLOR_TEXT_NEON_MAGENTA if self.game_over and not self.won else COLOR_TEXT_NEON_CYAN

            # Draw message with neon glow effect
            message_surface = fonts['message'].render(message_text, True, message_color)
            message_rect = message_surface.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT + SCORE_HEIGHT) // 2 - 50))
            # Determine glow color based on message color
            glow_color = (message_color[0], message_color[1], message_color[2], 50) # Semi-transparent glow color
            # Draw glow layers
            for offset in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]: # Slightly larger glow
                 glow_surface = fonts['message'].render(message_text, True, glow_color)
                 glow_rect = glow_surface.get_rect(center=(message_rect.centerx + offset[0], message_rect.centery + offset[1]))
                 screen.blit(glow_surface, glow_rect)
            screen.blit(message_surface, message_rect) # Draw original text on top


            restart_text = "[R]: REINITIALIZE SEQUENCE"
            restart_surface = fonts['medium'].render(restart_text, True, COLOR_TEXT_NEON_YELLOW)
            restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT + SCORE_HEIGHT) // 2 + 30))
            screen.blit(restart_surface, restart_rect)

            # Draw leaderboard
            leaderboard_title_surface = fonts['medium'].render("LEADERBOARD", True, COLOR_TEXT_NEON_YELLOW)
            leaderboard_title_rect = leaderboard_title_surface.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT + SCORE_HEIGHT) // 2 + 80))
            screen.blit(leaderboard_title_surface, leaderboard_title_rect)

            leaderboard_start_y = (SCREEN_HEIGHT + SCORE_HEIGHT) // 2 + 110
            for i, score in enumerate(self.leaderboard):
                score_text = f"{i+1}. {score}"
                score_surface = fonts['small'].render(score_text, True, COLOR_TEXT_LIGHT)
                score_rect = score_surface.get_rect(center=(SCREEN_WIDTH // 2, leaderboard_start_y + i * 30))
                screen.blit(score_surface, score_rect)

    def draw_menu(self, screen, fonts):
        """
        Draws the main menu screen.
        """
        screen.fill(COLOR_BACKGROUND)

        # Draw game title
        title_text = "CYBERPUNK 2048"
        title_surface = fonts['message'].render(title_text, True, COLOR_TEXT_NEON_CYAN)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(title_surface, title_rect)

        # Draw start message
        start_text = "[PRESS ANY KEY TO START]"
        start_surface = fonts['medium'].render(start_text, True, COLOR_TEXT_NEON_YELLOW)
        start_rect = start_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(start_surface, start_rect)

        # Draw leaderboard title on menu
        leaderboard_title_surface = fonts['medium'].render("LEADERBOARD", True, COLOR_TEXT_NEON_YELLOW)
        leaderboard_title_rect = leaderboard_title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(leaderboard_title_surface, leaderboard_title_rect)

        # Draw leaderboard scores on menu
        leaderboard_start_y = SCREEN_HEIGHT // 2 + 150
        for i, score in enumerate(self.leaderboard):
            score_text = f"{i+1}. {score}"
            score_surface = fonts['small'].render(score_text, True, COLOR_TEXT_LIGHT)
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH // 2, leaderboard_start_y + i * 25))
            screen.blit(score_surface, score_rect)


# Main game function
# This function is needed outside of the class to run the game

def main():
    """
    Main function to initialize pygame, create game instance, and run the game loop
    with Cyberpunk style.
    """
    pygame.init()
    pygame.mixer.init() # Initialize the mixer for sound effects
    logging.info("Initializing Pygame for Cyberpunk 2048...")

    # Load and play background music
    try:
        pygame.mixer.music.load("background.mp3") # Replace with your music file
        pygame.mixer.music.play(-1) # Play indefinitely
        logging.info("Background music loaded and playing.")
    except pygame.error as e:
        logging.warning(f"Could not load or play background music: {e}")


    # Create the screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CYBERPUNK 2048")

    # Load fonts - Try a cyberpunk-ish font, fallback to Arial/default
    fonts = {}
    try:
        # Attempt to use a more "techy" or "glitchy" font if available
        # Common monospace fonts often give a terminal/hacker feel
        fonts['large'] = pygame.font.SysFont(FONT_NAME_PRIMARY, FONT_SIZE_LARGE, bold=True)
        fonts['medium'] = pygame.font.SysFont(FONT_NAME_PRIMARY, FONT_SIZE_MEDIUM, bold=True)
        fonts['small'] = pygame.font.SysFont(FONT_NAME_PRIMARY, FONT_SIZE_SMALL, bold=True)
        fonts['score'] = pygame.font.SysFont(FONT_NAME_PRIMARY, FONT_SIZE_SCORE, bold=True)
        fonts['message'] = pygame.font.SysFont(FONT_NAME_PRIMARY, FONT_SIZE_MESSAGE, bold=True)
        logging.info(f"Successfully loaded '{FONT_NAME_PRIMARY}' font.")
    except pygame.error as e:
        logging.warning(f"Could not load '{FONT_NAME_PRIMARY}' font, using fallback '{FONT_NAME_FALLBACK}': {e}")
        try:
            fonts['large'] = pygame.font.SysFont(FONT_NAME_FALLBACK, FONT_SIZE_LARGE, bold=True)
            fonts['medium'] = pygame.font.SysFont(FONT_NAME_FALLBACK, FONT_SIZE_MEDIUM, bold=True)
            fonts['small'] = pygame.font.SysFont(FONT_NAME_FALLBACK, FONT_SIZE_SMALL, bold=True)
            fonts['score'] = pygame.font.SysFont(FONT_NAME_FALLBACK, FONT_SIZE_SCORE, bold=True)
            fonts['message'] = pygame.font.SysFont(FONT_NAME_FALLBACK, FONT_SIZE_MESSAGE, bold=True)
            logging.info(f"Successfully loaded fallback '{FONT_NAME_FALLBACK}' font.")
        except pygame.error as e_fallback:
            logging.error(f"Could not load system font '{FONT_NAME_FALLBACK}' nor default, critical error: {e_fallback}")
            # If even Arial fails, use pygame's default font (less control over boldness)
            fonts['large'] = pygame.font.Font(None, FONT_SIZE_LARGE + 5) # Approx bold
            fonts['medium'] = pygame.font.Font(None, FONT_SIZE_MEDIUM + 3)
            fonts['small'] = pygame.font.Font(None, FONT_SIZE_SMALL)
            fonts['score'] = pygame.font.Font(None, FONT_SIZE_SCORE + 3)
            fonts['message'] = pygame.font.Font(None, FONT_SIZE_MESSAGE + 5)
            logging.warning("Using Pygame's default unspecifed font.")


    # Create game instance
    game = Game2048()

    # Clock for controlling FPS
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.info("Termination signal received. Shutting down.")
                running = False
            elif event.type == pygame.KEYDOWN:
                if game.game_state == 'MENU':
                    # Any key press starts the game
                    game.game_state = 'PLAYING'
                    logging.info("Game state changed to PLAYING.")
                elif game.game_state == 'PLAYING':
                    if game.game_over or game.won:
                        if event.key == pygame.K_r:
                            logging.info("SYSTEM REBOOT: Initializing new game sequence.")
                            game = Game2048() # Create a new game instance to restart
                    elif not game.game_over : # Only process moves if game is not over
                        # moved = False # This variable isn't strictly necessary here as game.move returns it
                        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            game.move('left')
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            game.move('right')
                        elif event.key == pygame.K_UP or event.key == pygame.K_w:
                            game.move('up')
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            game.move('down')
                        # No need to explicitly call game.is_game_over() here
                        # as game.move -> game.move_left -> add_random_tile / is_game_over path handles it
                elif game.game_state in ['GAME_OVER', 'WON']:
                     if event.key == pygame.K_r:
                        logging.info("SYSTEM REBOOT: Initializing new game sequence.")
                        game = Game2048() # Create a new game instance to restart


        # Update effect timers (even if not currently used by the simple flash)
        # This is a placeholder for more complex effects later
        if game.game_over:
            game.game_over_effect_timer += clock.get_time()
        if game.won:
            game.win_effect_timer += clock.get_time()

        # Draw everything based on game state
        if game.game_state == 'MENU':
            game.draw_menu(screen, fonts)
        elif game.game_state == 'PLAYING':
            game.draw(screen, fonts) # Draw game board and score
        elif game.game_state in ['GAME_OVER', 'WON']:
             game.draw(screen, fonts) # Draw game board, score, and game over/win overlay (handled in draw)


        # Add scanline effect for cyberpunk feel (apply to all states for consistency)
        for y in range(0, SCREEN_HEIGHT, 3): # Draw lines every 3 pixels
            pygame.draw.line(screen, (0, 0, 0, 30), (0, y), (SCREEN_WIDTH, y), 1) # Semi-transparent black lines

        # Add simple glitch effect (apply to all states for consistency)
        if random.random() < 0.1: # Apply glitch effect with a 10% probability each frame
            glitch_area_y = random.randint(0, SCREEN_HEIGHT - 20) # Random vertical position (apply to full screen now)
            glitch_height = random.randint(5, 15) # Random height of the glitch area
            glitch_offset = random.randint(-10, 10) # Random horizontal offset

            # Ensure the glitch area is within bounds
            glitch_area_y = max(0, glitch_area_y)
            glitch_area_y = min(SCREEN_HEIGHT - glitch_height, glitch_area_y)

            # Create a sub-surface of the area to glitch
            glitch_surface = screen.subsurface((0, glitch_area_y, SCREEN_WIDTH, glitch_height)).copy()

            # Draw the glitched sub-surface with an offset
            screen.blit(glitch_surface, (glitch_offset, glitch_area_y))


        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(FPS)

    pygame.quit()
    logging.info("Pygame instance terminated.")
    sys.exit()

# This line is outside any class and calls the main function to start the game
# This block is outside any class and runs the main function when the script is executed
if __name__ == '__main__':
    main()
