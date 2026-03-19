import pygame
import chess
import chess.engine
import sys

# --- Constants ---
WIDTH, HEIGHT = 640, 640
DIMENSION = 8  # 8x8 chessboard
SQ_SIZE = WIDTH // DIMENSION
FPS = 15

# Colors
WHITE = (240, 217, 181)
BROWN = (181, 136, 99)
HIGHLIGHT = (100, 200, 100)

# Unicode chess symbols
UNICODE_PIECES = {
    'r': '♜', 'kn': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
    'Rw': '♖', 'knw': '♘', 'Bw': '♗', 'Qw': '♕', 'Kw': '♔', 'pw': '♙'
}

pygame.font.init()
PIECE_FONT = pygame.font.SysFont('dejavusans', SQ_SIZE - 10)

# --- Loading images ---
def load_images():
    images = {}
    pieces = ['r', 'kn', 'b', 'q', 'k', 'p', 'Rw', 'knw', 'Bw', 'Qw', 'Kw', 'pw']
    for piece in pieces:
        try:
            # Replace this with actual image loading if you have image files.
            # For now, it will use a simple font rendering to show the piece symbol.
            images[piece] = PIECE_FONT.render(UNICODE_PIECES[piece], True, (0, 0, 0))
        except KeyError as e:
            print(f"Missing piece in UNICODE_PIECES for: {e}")
    return images

IMAGES = load_images()

def draw_board(screen):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = WHITE if (row + col) % 2 == 0 else BROWN
            pygame.draw.rect(screen, color, pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - square // 8
            col = square % 8
            piece_symbol = piece.symbol()
            if piece_symbol in IMAGES:
                piece_surface = IMAGES[piece_symbol]
                text_rect = piece_surface.get_rect(center=(col * SQ_SIZE + SQ_SIZE // 2, row * SQ_SIZE + SQ_SIZE // 2))
                screen.blit(piece_surface, text_rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess vs Stockfish")
    clock = pygame.time.Clock()
    screen.fill(pygame.Color("white"))

    board = chess.Board()

    # Initialize Stockfish engine
    STOCKFISH_PATH = "C:/Users/rudra/program_languages/game engines/stockfish/stockfish-windows-x86-64-avx2.exe"
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        engine.configure({"Skill Level": 1})
    except Exception as e:
        print("Error starting Stockfish:", e)
        sys.exit(1)

    running = True
    selected_square = None
    move_made = False

    while running:
        draw_board(screen)
        draw_pieces(screen, board)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and board.turn == chess.WHITE:
                location = pygame.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = 7 - (location[1] // SQ_SIZE)
                square = chess.square(col, row)

                if selected_square is None:
                    if board.piece_at(square) and board.piece_at(square).color == board.turn:
                        selected_square = square
                else:
                    move = chess.Move(selected_square, square)
                    if move in board.legal_moves:
                        board.push(move)
                        move_made = True
                    selected_square = None

        if move_made and not board.is_game_over():
            print("Stockfish is thinking...")
            result = engine.play(board, chess.engine.Limit(time=0.5))
            print("Stockfish plays:", result.move.uci())
            board.push(result.move)
            move_made = False

        pygame.display.flip()
        clock.tick(FPS)

    print("Game over!")
    print("Result:", board.result())
    engine.quit()
    pygame.quit()

if __name__ == "__main__":
    main()
