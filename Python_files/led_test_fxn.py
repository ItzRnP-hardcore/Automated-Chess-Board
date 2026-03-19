import time
import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color
import chess

# LED Strip Configuration
LED_COUNT = 64        # Number of LED pixels
LED_PIN = 18          # GPIO pin (PWM required)
LED_FREQ_HZ = 800000  # LED signal frequency
LED_DMA = 10          # DMA channel
LED_BRIGHTNESS = 128  # Brightness (0-255)
LED_INVERT = False    # Invert signal (for NPN transistor level shift)
LED_CHANNEL = 0       # PWM channel

# Initialize LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Colors
CYAN_GREEN = Color(0, 255, 128)
LIGHT_BLUE = Color(0, 128, 255)
RED_ORANGE = Color(255, 69, 0)
CHECK_RED = Color(255, 0, 0)
BLUE = Color(0, 0, 255)
BLACK = Color(0, 0, 0)

def square_to_index(square):
    """
    Convert a chess square (int) to an LED index using a snake pattern.
    Even ranks map left-to-right, odd ranks map right-to-left.
    """
    rank = chess.square_rank(square)
    file = chess.square_file(square)
    if rank % 2 == 0:
        return (7 - rank) * 8 + file
    else:
        return (7 - rank) * 8 + (7 - file)

def set_led(index, color):
    """Set a specific LED to a given color."""
    if 0 <= index < LED_COUNT:
        strip.setPixelColor(index, color)
        strip.show()

def highlight_moves(chess_board, piece_square):
    """Highlight legal moves for a selected piece."""
    clear_leds()
    legal_moves = [m for m in chess_board.legal_moves if m.from_square == piece_square]
    for move in legal_moves:
        if move.from_square == piece_square:
            target_index = square_to_index(move.to_square)
            if chess_board.is_capture(move):
                set_led(target_index, RED_ORANGE)
            else:
                set_led(target_index, LIGHT_BLUE)

def check_warning(chess_board):
    """Blink the king's LED if the current player is in check."""
    if chess_board.is_check():
        king_square = chess_board.king(chess_board.turn)
        if king_square is not None:
            king_index = square_to_index(king_square)
            for _ in range(2):
                set_led(king_index, CHECK_RED)
                time.sleep(0.5)
                set_led(king_index, BLACK)
                time.sleep(0.5)
def checkmate_warning(chess_board):
    """Blink the entire board 5 times and then make the winning side glow red."""
    if chess_board.is_checkmate():
        # Blink the entire board red 5 times
        for _ in range(5):
            for i in range(LED_COUNT):
                set_led(i, CHECK_RED)
            time.sleep(0.5)
            clear_leds()
            time.sleep(0.5)

        # Determine winner (opponent of the current turn lost)
        winning_side = not chess_board.turn  # True = White won, False = Black won

        # Make all winner's pieces glow red
        for square in chess.SQUARES:
            piece = chess_board.piece_at(square)
            if piece and piece.color == winning_side:
                set_led(square_to_index(square), CHECK_RED)

def update_board_display(move):
    """Update LEDs to show the last move."""
    clear_leds()
    set_led(square_to_index(move.from_square), CYAN_GREEN)
    set_led(square_to_index(move.to), BLUE)

def ai_move_display(move):
    """Show AI move on the LED board."""
    clear_leds()
    set_led(square_to_index(move.from_square), CYAN_GREEN)
    set_led(square_to_index(move.to_square), BLUE)

def clear_leds():
    """Turn off all LEDs."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, BLACK)
    strip.show()

