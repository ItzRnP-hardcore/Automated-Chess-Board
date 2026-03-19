import board
import neopixel
import time
import chess
import chess.engine

# Setup NeoPixel matrix
NUM_PIXELS = 64
pixels = neopixel.NeoPixel(board.D18, NUM_PIXELS, brightness=0.5, auto_write=False)

# Colors
CYAN_GREEN = (0, 255, 128)
LIGHT_BLUE = (0, 128, 255)
RED_ORANGE = (255, 69, 0)
CHECK_RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Chessboard coordinates mapping to NeoPixel index
def square_to_index(square):
    rank = chess.square_rank(square)
    file = chess.square_file(square)
    if rank % 2 == 0:
        return (7 - rank) * 8 + file  # Even ranks follow left-to-right
    else:
        return (7 - rank) * 8 + (7 - file)  # Odd ranks follow right-to-left (snake pattern)

# Light up possible moves
def highlight_moves(board, piece_square):
    legal_moves = list(board.legal_moves)
    for move in legal_moves:
        if move.from_square == piece_square:
            target_index = square_to_index(move.to_square)
            if board.is_capture(move):
                pixels[target_index] = RED_ORANGE  # Capturable piece
            else:
                pixels[target_index] = LIGHT_BLUE  # Regular move
    pixels.show()

# Blink if king is in check
def check_warning(board):
    if board.is_check():
        king_square = board.king(board.turn)
        if king_square:
            king_index = square_to_index(king_square)
            for _ in range(2):
                pixels[king_index] = CHECK_RED
                pixels.show()
                time.sleep(0.5)
                pixels[king_index] = BLACK
                pixels.show()
                time.sleep(0.5)

# Update board after a move
def update_board_display(move_from, move_to):
    pixels.fill(BLACK)
    pixels[square_to_index(move_from)] = CYAN_GREEN
    pixels[square_to_index(move_to)] = BLUE
    pixels.show()

def ai_move_display(move):
    pixels.fill(BLACK)
    pixels[square_to_index(move.from_square)] = CYAN_GREEN
    pixels[square_to_index(move.to_square)] = BLUE
    pixels.show()

# Example Usage:
if __name__ == "__main__":
    board = chess.Board()
    picked_square = chess.parse_square("e2")  # Example of a piece being picked up
    highlight_moves(board, picked_square)
    time.sleep(2)
    move = chess.Move.from_uci("e2e4")  # Example move
    update_board_display(move.from_square, move.to_square)
    check_warning(board)
    time.sleep(2)
