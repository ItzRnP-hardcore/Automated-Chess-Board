"""
Module: actuator_output_testfxn
Description:
    This module provides actuator control functions for a CoreXY-based chessboard.
    It includes functions for moving pieces, handling capture moves, homing axes, and calibration.
    
Usage Example:
    import actuator_output_testfxn as actuator

    # Home the system
    actuator.home_corexy()

    # Move a piece normally
    actuator.move_piece_with_stepper("e2e4")

    # Execute a capture move (using the special path)
    actuator.capture_move("e2e4", "h8")

    # Calibrate A1 to a new position (in mm)
    actuator.calibrate_a1((20, 20))
"""

__all__ = [
    "chess_square_to_xy",
    "move_to_xy",
    "move_piece_with_stepper",
    "capture_move",
    "home_x",
    "home_y",
    "home_corexy",
    "calibrate_a1",
    "get_current_position",
    "get_uci_move"
]

import RPi.GPIO as GPIO
import time
import re

# --- GPIO Pin Definitions ---
MOTOR1_STEP = 33  # Motor A Step (e.g., GPIO6 on BOARD numbering)
MOTOR1_DIR  = 31  # Motor A Direction (e.g., GPIO13)
MOTOR2_STEP = 37  # Motor B Step (e.g., GPIO19)
MOTOR2_DIR  = 35  # Motor B Direction (e.g., GPIO26)
MOTOR_ENAB  = 36

# Limit switches for homing
LIMIT_X = 29  # Horizontal limit switch (for X axis)
LIMIT_Y = 32  # Vertical limit switch (for Y axis)

# --- Global Configuration ---
HOME_X_OFFSET = 500  # Homing offset for the X axis in mm
HOME_Y_OFFSET = 0    # Homing offset for the Y axis in mm (50cm = 500mm)
SQUARE_SIZE = 40     # Chess square size in mm
HALF_SQUARE = SQUARE_SIZE / 2  # 20 mm

a1_calibration = None

# --- GPIO Setup ---
GPIO.setmode(GPIO.BOARD)
GPIO.setup(MOTOR1_STEP, GPIO.OUT)
GPIO.setup(MOTOR1_DIR, GPIO.OUT)
GPIO.setup(MOTOR2_STEP, GPIO.OUT)
GPIO.setup(MOTOR2_DIR, GPIO.OUT)
GPIO.setup(MOTOR_ENAB, GPIO.OUT)

GPIO.setup(LIMIT_X, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LIMIT_Y, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- Chess and Position Functions ---
def chess_square_to_xy(square):
    """
    Convert a chess square in algebraic notation (e.g., "e2") 
    to (x, y) coordinates in mm.
    The bottom-left square (a1) is centered at (20, 20) by default.
    """
    files = "abcdefgh"
    file = square[0]
    rank = int(square[1])
    col = ord(file) - ord('a')
    row = rank - 1
    x = col * SQUARE_SIZE + HALF_SQUARE
    y = row * SQUARE_SIZE + HALF_SQUARE
    return (x, y)

# --- Position Tracking ---
current_position = chess_square_to_xy("a1")
def get_current_position():
    return current_position

# --- electromagnet Functions ---
def magnet(power = False):

    # add electromagnet functionality
    if(power):
        print("grabbing chess piece...")
    else:
        print("releasing chess piece...")


# --- Motor Movement Logic ---
def move_to_xy(target_xy):
    """
    Move from the current position to the target (x, y) coordinate.
    Uses CoreXY logic to compute motor steps.
    """
    global current_position
    dx = target_xy[0] - current_position[0]
    dy = target_xy[1] - current_position[1]

    # CoreXY step calculations:
    dA = dx + dy
    dB = dy - dx

    steps_per_mm = 5  # Adjust based on your motor resolution
    steps_A = int(dA * steps_per_mm)
    steps_B = int(dB * steps_per_mm)

    print(f"Moving from {current_position} to {target_xy}")
    print(f"dx: {dx:.1f} mm, dy: {dy:.1f} mm")
    print(f"Motor A: {steps_A} steps, Motor B: {steps_B} steps")

    dir_A = GPIO.HIGH if steps_A > 0 else GPIO.LOW
    dir_B = GPIO.HIGH if steps_B > 0 else GPIO.LOW

    steps_A = abs(steps_A)
    steps_B = abs(steps_B)

    GPIO.output(MOTOR_ENAB, GPIO.LOW)  # Enable motors (active low)
    GPIO.output(MOTOR1_DIR, dir_A)
    GPIO.output(MOTOR2_DIR, dir_B)

    for i in range(max(steps_A, steps_B)):
        if i < steps_A:
            GPIO.output(MOTOR1_STEP, GPIO.HIGH)
        if i < steps_B:
            GPIO.output(MOTOR2_STEP, GPIO.HIGH)
        time.sleep(0.002)
        GPIO.output(MOTOR1_STEP, GPIO.LOW)
        GPIO.output(MOTOR2_STEP, GPIO.LOW)
        time.sleep(0.002)
    GPIO.output(MOTOR_ENAB, GPIO.HIGH)  # Disable motors
    current_position = target_xy

def move_piece_with_stepper(move_uci, special=False):
    """
    Convert a UCI move (e.g., "e2e4") into motor commands.
    
    For normal moves, the piece moves directly (with a simple intermediate point).
    For special moves (capture removal, knight moves, or castling), it follows this path:
      1. Move along X for half a square from the start.
      2. Move along Y until destination Y offset by half a square.
      3. Move along X to destination X.
      4. Move the final half square along Y to reach destination.
    
    Parameters:
      move_uci (str): UCI move string.
      special (bool): If True, use the detailed edge path.
    """
    start_square = move_uci[:2]
    end_square = move_uci[2:]
    
    start_xy = chess_square_to_xy(start_square)
    end_xy = chess_square_to_xy(end_square)
    
    print(f"\nPreparing to move piece: {move_uci}")
    print(f"Start square {start_square}: {start_xy}")
    print(f"End square {end_square}: {end_xy}")
    
    if current_position != start_xy:
        print("Moving to the start square...")
        move_to_xy(start_xy)

    magnet(power=True)

    if special:
        # Determine directions for half-square moves.
        dx = end_xy[0] - start_xy[0]
        dy = end_xy[1] - start_xy[1]
        sign_x = 1 if dx >= 0 else -1
        sign_y = 1 if dy >= 0 else -1

        # Segment 1: Move along X by half a square.
        p1 = (start_xy[0] + sign_x * HALF_SQUARE, start_xy[1])
        print(f"Segment 1 (X half square): Moving to {p1}")
        move_to_xy(p1)
        
        # Segment 2: Move along Y until reaching destination Y offset by half a square.
        p2 = (p1[0], end_xy[1] - sign_y * HALF_SQUARE)
        print(f"Segment 2 (Y to near destination): Moving to {p2}")
        move_to_xy(p2)
        
        # Segment 3: Move along X to destination X.
        p3 = (end_xy[0], p2[1])
        print(f"Segment 3 (X to destination): Moving to {p3}")
        move_to_xy(p3)
        
        # Segment 4: Final half-square move along Y.
        print(f"Segment 4 (Final Y half square): Moving to {end_xy}")
        move_to_xy(end_xy)
    else:
        # --- NORMAL MOVE (DIAGONAL) ---
        print("Moving piece directly from start to end square (diagonal).")
        move_to_xy(end_xy)
    magnet()
    print(f"Piece moved. Current position is now: {current_position}")

def capture_move(capturing_uci, captured_dest_square):
    """
    Handles a capture event:
      1. Moves the captured piece (currently on the destination square of the capturing move)
         to its designated capture square using the special path.
      2. Then moves the capturing piece from its start square to the destination square using the special path.
    
    Parameters:
      capturing_uci (str): UCI move string (e.g., "e2e4") representing the capturing move.
      captured_dest_square (str): Designated destination square for the captured piece.
    """
    # Extract squares from the capturing move.
    capturing_start_square = capturing_uci[:2]
    capturing_end_square = capturing_uci[2:]
    
    # Construct a move string for the captured piece.
    # The captured piece is originally on capturing_end_square.
    captured_move_uci = capturing_end_square + captured_dest_square
    
    print("\nCapture event detected.")
    print("Moving captured piece to its designated square using special path...")
    move_piece_with_stepper(captured_move_uci, special=True)
    
    print("Moving capturing piece to its destination using special path...")
    move_piece_with_stepper(capturing_uci, special=True)

def castle_move(king_castling_uci, castling_side):
    """
    Handles castling moves. The procedure is as follows:
      1. The king is lifted (moved vertically by half a square) to an intermediate "edge" position.
      2. The king then travels horizontally along that edge until it is aligned with its final square.
      3. The tool remains there while the rook is moved from its starting square to its destination square,
         based on whether castling is kingside or queenside.
      4. Finally, the king is moved vertically by half a square into its final square.
    
    Parameters:
      king_castling_uci (str): UCI move string for the king (e.g., "e1g1" for white kingside castling).
      castling_side (str): "kingside" or "queenside", indicating which rook to move.
    """
    # Extract king start and final squares from the UCI string.
    king_start_square = king_castling_uci[:2]
    king_final_square = king_castling_uci[2:]
    
    k_start = chess_square_to_xy(king_start_square)
    k_end   = chess_square_to_xy(king_final_square)
    
    # Determine vertical movement direction based on king's starting rank:
    # White king (rank '1'): move upward; Black king (rank '8'): move downward.
    sign_y = 1 if king_start_square[1] == '1' else -1

    # Calculate king intermediate positions.
    # Step 1: Lift the king vertically by half a square.
    king_intermediate1 = (k_start[0], k_start[1] + sign_y * HALF_SQUARE)
    # Step 2: Move horizontally to align with final square x coordinate.
    king_intermediate2 = (k_end[0], king_intermediate1[1])
    
    print("\nCastling move detected.")
    print("Moving king to intermediate edge position...")
    # Move king from starting square to intermediate1 (vertical lift)
    move_to_xy(king_intermediate1)
    # Move horizontally along the edge to align with final x.
    move_to_xy(king_intermediate2)
    
    # --- Rook Movement ---
    # Determine king color based on its starting rank.
    king_color = "white" if king_start_square[1] == '1' else "black"
    
    # Set rook start and end squares based on king color and castling side.
    if king_color == "white":
        if castling_side == "kingside":
            rook_start_square, rook_end_square = "h1", "f1"
        elif castling_side == "queenside":
            rook_start_square, rook_end_square = "a1", "d1"
        else:
            raise ValueError("Invalid castling_side. Use 'kingside' or 'queenside'.")
    else:  # black
        if castling_side == "kingside":
            rook_start_square, rook_end_square = "h8", "f8"
        elif castling_side == "queenside":
            rook_start_square, rook_end_square = "a8", "d8"
        else:
            raise ValueError("Invalid castling_side. Use 'kingside' or 'queenside'.")
    
    r_start = chess_square_to_xy(rook_start_square)
    r_end   = chess_square_to_xy(rook_end_square)
    
    print("Moving rook for castling...")
    # Save current position (which is at king_intermediate2).
    saved_position = get_current_position()
    # Move tool to the rook's starting square.
    move_to_xy(r_start)
    # Move the rook directly (normal move; can go diagonally if needed).
    move_to_xy(r_end)
    # Return tool to king intermediate position.
    move_to_xy(saved_position)
    
    # --- Final King Move ---
    print("Moving king into final square...")
    # Move king from intermediate position to final destination (vertical drop).
    move_to_xy(k_end)
    print("Castling complete.")


# --- Homing Functions ---
def home_x(delay=0.002):
    print("Homing horizontal (X) axis...")
    GPIO.output(MOTOR1_DIR, GPIO.LOW)
    GPIO.output(MOTOR2_DIR, GPIO.HIGH)
    while GPIO.input(LIMIT_X) == GPIO.HIGH:
        GPIO.output(MOTOR1_STEP, GPIO.HIGH)
        GPIO.output(MOTOR2_STEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(MOTOR1_STEP, GPIO.LOW)
        GPIO.output(MOTOR2_STEP, GPIO.LOW)
        time.sleep(delay)
    print("Horizontal axis homed.")

def home_y(delay=0.002):
    print("Homing vertical (Y) axis...")
    GPIO.output(MOTOR1_DIR, GPIO.LOW)
    GPIO.output(MOTOR2_DIR, GPIO.LOW)
    while GPIO.input(LIMIT_Y) == GPIO.HIGH:
        GPIO.output(MOTOR1_STEP, GPIO.HIGH)
        GPIO.output(MOTOR2_STEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(MOTOR1_STEP, GPIO.LOW)
        GPIO.output(MOTOR2_STEP, GPIO.LOW)
        time.sleep(delay)
    print("Vertical axis homed.")

def home_corexy():
    global current_position
    print("Starting CoreXY homing process...")
    home_x()
    home_y()
    current_position = (HOME_X_OFFSET, HOME_Y_OFFSET)
    print(f"CoreXY homing complete. Current position set to {current_position}.")

# --- Calibration Function ---
def calibrate_a1(new_a1_position):
    global a1_calibration, current_position
    a1_calibration = new_a1_position
    current_position = new_a1_position
    print(f"Calibrated A1 to {a1_calibration}")

# --- UCI Input ---
def get_uci_move():
    uci_pattern = re.compile(r"^[a-h][1-8][a-h][1-8]$")
    move = input("Enter a move in UCI format (e.g., e2e4): ").strip().lower()
    return move if uci_pattern.match(move) else None
