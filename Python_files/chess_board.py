import chess
import chess.engine
import sys
import RPi.GPIO as GPIO
import actautor_output_testfxn as actuator
import input_sensor_testfxn as sensor
import led_test_fxn as led
import time

# Multiplexer Pins
select_pins = [19, 21, 23, 24]
enab_pins = [11, 13, 15, 16]
output_pin = 12                         


"""
select_pins = [19, 21, 23, 24]
✅ Fix: If you're not using SPI, you can still use them as GPIOs.

Disable SPI by running:

in sh terminal
sudo raspi-config

Go to Interface Options → SPI → Disable.

Reboot the Raspberry Pi.
"""


# Initialize sensor module
Input = sensor.ChessInputHandler(select_pins, enab_pins, output_pin)

def main():
    # Correct Stockfish Path for Raspberry Pi
    STOCKFISH_PATH = "/usr/games/stockfish"
    
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        engine.configure({"Skill Level": 1})
    except Exception as e:
        print("Error starting Stockfish:", e)
        sys.exit(1)

    board = chess.Board()
    print("Welcome to Chess with Stockfish!")
    print("Move a piece using the chessboard sensors.")
    print("Type 'quit' to exit.\n")

    while not board.is_game_over():
        print(board, "\n")
        
        if board.turn == chess.WHITE:

            led.check_warning(board)
            print("Waiting for your move...")

            try:
                move = Input.detect_move(board)  # Read move from sensor
                if move in board.legal_moves:
                    print(f"Your move: {move.uci()}")
                    board.push(move)

                    # Highlight move on LED board
                    #led.update_board_display(move)  already done in the input sensor

                    # Move piece using actuators
                    # actuator.move_piece(move.from_square, move.to_square)  no need to move piece when player is moving
                else:
                    print("Illegal move detected! Try again.")
                    continue
            except Exception:
                print("Invalid move detected! Try again.")
                continue

        else:
            # Stockfish's move
            print("Stockfish is thinking...\n")
            result = engine.play(board, chess.engine.Limit(time=0.1))
            print("Stockfish plays:", result.move.uci(), "\n")
            board.push(result.move)

            # Show Stockfish's move on LEDs
            led.ai_move_display(result.move)

            # Actuate Stockfish's move
            actuator.move_piece(result.move.from_square, result.move.to_square)
            time.sleep(0.5)
            Input.save_current_state_as_previous()

    led.checkmate_warning(board)
    print("Game over!")
    print("Result:", board.result())
    engine.quit()
    GPIO.cleanup()

if __name__ == "__main__":
    main()
