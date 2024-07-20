import board
import displayio
import adafruit_matrixportal.matrix
import random
import time
import digitalio
import adafruit_lis3dh

# Try to import the accelerometer library
try:
    from adafruit_lis3dh import LIS3DH_I2C
    has_accelerometer_lib = True
except ImportError:
    has_accelerometer_lib = False
    print("LIS3DH library not found. Accelerometer functionality will be disabled.")

# Initialize the matrix
matrix = adafruit_matrixportal.matrix.Matrix(width=64, height=32, bit_depth=4)
display = matrix.display

# Set up accelerometer
has_accelerometer = False
if has_accelerometer_lib:
    try:
        i2c = board.I2C()  # uses board.SCL and board.SDA
        lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)
        has_accelerometer = True
        print("Accelerometer initialized successfully")
    except Exception as e:
        print(f"Failed to initialize accelerometer: {e}")
        print("Continuing without accelerometer functionality.")

# Set up buttons
button_up = digitalio.DigitalInOut(board.BUTTON_UP)
button_up.switch_to_input(pull=digitalio.Pull.UP)
button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
button_down.switch_to_input(pull=digitalio.Pull.UP)

# Tetris constants
BOARD_WIDTH = 64  # Adjusted to fit the 64-pixel width
BOARD_HEIGHT = 32  # Height remains the same
BLOCK_SIZE = 1

# Tetromino shapes oriented to fall from the right
SHAPES = [
    [[1, 1, 1, 1, 1, 1],[1, 1, 1, 1, 1, 1],[1, 1, 1, 1, 1, 1]],  # Large I shape
    [[1, 1, 1, 1],[1, 1, 1, 1],[1, 1, 1, 1],[1, 1, 1, 1]],  # Large O shape
    [[1, 1, 1, 1, 1, 1],[1, 1, 1, 1, 1, 1], [0, 0, 1, 1, 0, 0], [0, 0, 1, 1, 0, 0], [0, 0, 1, 1, 0, 0]],  # Large T shape
    [[1, 1, 1, 1, 1, 1],[1, 1, 1, 1, 1, 1],[1, 1, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0]],  # Large L shape
    [[1, 1, 1, 1, 1, 1],[1, 1, 1, 1, 1, 1],[0, 0, 0, 0, 1, 1], [0, 0, 0, 0, 1, 1], [0, 0, 0, 0, 1, 1]],  # Large J shape
    [[0, 0, 1, 1, 1, 1],[0, 0, 1, 1, 1, 1],[1, 1, 1, 1, 0, 0],[1, 1, 1, 1, 0, 0]],  # Large S shape
    [[1, 1, 1, 1, 0, 0],[1, 1, 1, 1, 0, 0],[0, 0, 1, 1, 1, 1],[0, 0, 1, 1, 1, 1]]  # Large Z shape
]



# Colors for each shape
COLORS = [0x6825CF, 0xCF2577, 0x2528CF, 0x2594CF, 0x1DB82B, 0xFF8000, 0xED0000]

# Initialize game board
game_board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

# Create a bitmap and palette for drawing
bitmap = displayio.Bitmap(BOARD_WIDTH, BOARD_HEIGHT, len(COLORS) + 1)
palette = displayio.Palette(len(COLORS) + 1)
palette[0] = 0  # Background color (black)
for i, color in enumerate(COLORS):
    palette[i + 1] = color

# Create a TileGrid using the bitmap and palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

# A Group to hold the game elements
game_group = displayio.Group()
game_group.append(tile_grid)
display.show(game_group)

# The tetromino state
current_tetromino = None
current_position = [0, 0]

#BLURRGGGGGGG!!!!!!

# Function to draw a block on the LED matrix
def draw_block(x, y, color_index):
    if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
        bitmap[x, y] = color_index + 1

# Function to clear the LED matrix
def clear_display():
    bitmap.fill(0)

# Function to generate a new tetromino
def new_tetromino():
    global current_tetromino, current_position
    current_tetromino = random.choice(SHAPES)
    current_position = [BOARD_WIDTH - len(current_tetromino[0]), BOARD_HEIGHT // 2 - len(current_tetromino) // 2]

# Function to check for collisions
def check_collision(offset_x=0, offset_y=0):
    for y, row in enumerate(current_tetromino):
        for x, cell in enumerate(row):
            if cell:
                board_x = current_position[0] + x + offset_x
                board_y = current_position[1] + y + offset_y
                if (board_x < 0 or board_x >= BOARD_WIDTH or
                    board_y < 0 or board_y >= BOARD_HEIGHT or
                    (board_y >= 0 and game_board[board_y][board_x])):
                    return True
    return False

# Function to move the tetromino
def move_tetromino(dx, dy):
    global current_position
    if not check_collision(dx, dy):
        current_position[0] += dx
        current_position[1] += dy
        return True
    return False

# Function to rotate the tetromino
def rotate_tetromino():
    global current_tetromino
    rotated = list(zip(*current_tetromino[::-1]))
    if not check_collision():
        current_tetromino = rotated

# Function to place the tetromino on the board
def place_tetromino():
    for y, row in enumerate(current_tetromino):
        for x, cell in enumerate(row):
            if cell:
                board_y = current_position[1] + y
                board_x = current_position[0] + x
                if 0 <= board_y < BOARD_HEIGHT and 0 <= board_x < BOARD_WIDTH:
                    game_board[board_y][board_x] = SHAPES.index(current_tetromino) + 1

# Function to clear completed lines
def clear_lines():
    global game_board
    new_board = [row for row in game_board if not all(row)]
    lines_cleared = BOARD_HEIGHT - len(new_board)
    game_board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(lines_cleared)] + new_board

# Function to draw the current game state
def draw_game_state():
    # Draw the game board
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            if game_board[y][x] != 0:
                draw_block(x, y, game_board[y][x] - 1)

    # Draw the current tetromino
    if current_tetromino:
        for y, row in enumerate(current_tetromino):
            for x, cell in enumerate(row):
                if cell:
                    draw_block(current_position[0] + x, current_position[1] + y,
                               SHAPES.index(current_tetromino))

# Function to display "Game Over" message
def display_game_over():
    clear_display()
    game_over_text = "GAME OVER"
    x = (BOARD_WIDTH - len(game_over_text) * 4) // 2  # Center text horizontally
    for i, char in enumerate(game_over_text):
        draw_text(char, x + i * 4, 12, 0xFF0000)  # Adjust positions as necessary
    display.refresh()
    time.sleep(2)  # Display the message for 2 seconds

# Function to draw text on the LED matrix
def draw_text(char, x, y, color):
    font_data = {
        'A': [[0,1,0],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
        'B': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,1,0]],
        'C': [[0,1,1],[1,0,0],[1,0,0],[1,0,0],[0,1,1]],
        'E': [[1,1,1],[1,0,0],[1,1,0],[1,0,0],[1,1,1]],
        'G': [[0,1,1],[1,0,0],[1,1,1],[1,0,1],[0,1,1]],
        'M': [[1,0,0,1],[1,1,1,1],[1,0,1,1],[1,0,0,1]],
        'O': [[0,1,0],[1,0,1],[1,0,1],[1,0,1],[0,1,0]],
        'R': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
        'V': [[1,0,0,1],[1,0,0,1],[0,1,0,1],[0,1,0,1],[0,0,1,0]],
        'G': [[1,1,1,1,1], [1,1,1,1,1], [1,1,1,1,1], [1,1,1,1,1]]
    }
    font = font_data.get(char, [])
    for dy, row in enumerate(font):
        for dx, pixel in enumerate(row):
            if pixel:
                draw_block(x + dx, y + dy, color)

# Function to draw color-coded borders
def draw_borders():
    # Top border (Red)
    for x in range(BOARD_WIDTH):
        draw_block(x, 0, 0)  # 0 is the index for red in COLORS

    # Right border (Green)
    for y in range(BOARD_HEIGHT):
        draw_block(BOARD_WIDTH - 1, y, 1)  # 1 is the index for green

    # Bottom border (Blue)
    for x in range(BOARD_WIDTH):
        draw_block(x, BOARD_HEIGHT - 1, 2)  # 2 is the index for blue

    # Left border (Yellow)
    for y in range(BOARD_HEIGHT):
        draw_block(0, y, 3)  # 3 is the index for yellow

ACCEL_THRESHOLD = 0.5  # Threshold for detecting tilt
MOVE_INTERVAL = 0.01  # Time between movements when tilted

# Function to determine movement direction based on accelerometer data
def get_move_direction(x):
    if x > ACCEL_THRESHOLD:
        return 1  # Move down
    elif x < -ACCEL_THRESHOLD:
        return -1  # Move up
    return 0  # No movement

# Modify the new_tetromino function
def new_tetromino():
    global current_tetromino, current_position
    current_tetromino = random.choice(SHAPES)
    # Start the tetromino at the top center
    start_x = (BOARD_WIDTH - len(current_tetromino[0]))
    start_y = (BOARD_HEIGHT - len(current_tetromino[0])) // 2
    current_position = [start_x, start_y]

# Modify the game_loop function
def game_loop():
    last_fall_time = time.monotonic()
    last_accel_move_time = time.monotonic()
    button_interval = 0.3
    fall_interval = 0.1  # Time between automatic falling movements

    # Draw the color-coded borders
    display.refresh()
    time.sleep(2)  # Display the borders for 2 seconds before starting the game

    while True:
        current_time = time.monotonic()

        # Handle button inputs
        if current_time - last_accel_move_time > button_interval:
            if not button_up.value:
                move_tetromino(0, -1)  # Move up
            if not button_down.value:
                move_tetromino(0, 1)  # Move down
            last_accel_move_time = current_time

        # Read accelerometer data if available
        if has_accelerometer:
            try:
                x, y, z = lis3dh.acceleration
                #print(f"Accelerometer values: x={x:.2f}, y={y:.2f}, z={z:.2f}")  # Debug output

                # Determine movement direction (up/down based on x-axis tilt)
                move_dir = get_move_direction(y)

                # Move based on accelerometer tilt
                if move_dir != 0 and current_time - last_accel_move_time > MOVE_INTERVAL:
                    if move_tetromino(0, move_dir):
                        last_accel_move_time = current_time
                        #print(f"Moved {'up' if move_dir == -1 else 'down'} based on tilt")  # Debug output

                # Rotate if z-axis tilted
                if abs(z) > 9:
                    rotate_tetromino()
                    print("Rotated tetromino")  # Debug output
            except OSError:
                print("Failed to read accelerometer. Continuing without accelerometer input.")

        # Move left (fall) periodically
        if current_time - last_fall_time > fall_interval:
            if not move_tetromino(-1, 0):
                # If can't move left, place the tetromino and get a new one
                place_tetromino()
                clear_lines()
                new_tetromino()
                if check_collision():
                    # Game over
                    display_game_over()
                    return
            last_fall_time = current_time

        # Update display
        clear_display()
        draw_game_state()
        display.refresh()
        time.sleep(0.01)  # Small delay to prevent hogging the CPU

game_board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

# Start the game loop immediately
while True:
    try:
        new_tetromino()
        game_loop()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Game stopped. Restarting...")
        time.sleep(2)  # Wait for 2 seconds before restarting
        # Reset the game board
        game_board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
