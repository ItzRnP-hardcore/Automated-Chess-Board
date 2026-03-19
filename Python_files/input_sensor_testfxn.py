import time
import chess
import RPi.GPIO as GPIO
import led_test_fxn as led_module

class ChessInputHandler:
    def __init__(self, select_pins, enable_pins, output_pin):
        """
        Initializes the sensor input handler with multiplexer control.
        """
        GPIO.setmode(GPIO.BOARD)  # Use BCM numbering
        
        self.select_pins = select_pins
        self.enable_pins = enable_pins
        self.output_pin = output_pin
        self.sensors_active = True  # Flag to enable/disable sensor detection
        
        for pin in self.select_pins + self.enable_pins:
            GPIO.setup(pin, GPIO.OUT)
        GPIO.setup(self.output_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.prev_state = self.read_sensor_array()
    
    def set_multiplexer_channel(self, mux_idx, channel):
        """
        Sets the multiplexer to read from a specific channel.
        """
        for i in range(4):
            GPIO.output(self.select_pins[i], (channel >> i) & 1)
        for i in range(len(self.enable_pins)):
            GPIO.output(self.enable_pins[i], 1 if i == mux_idx else 0)
    
    def read_sensor_array(self):
        """
        Reads sensor states using multiplexers.
        Returns a list of 64 integers:
          0: piece present
          1: square empty
        """
        state = [1] * 64  # Default to empty board
        for mux_idx in range(4):
            for channel in range(16):
                self.set_multiplexer_channel(mux_idx, channel)
                time.sleep(0.00001)  # Allow signal to stabilize
                state[mux_idx * 16 + channel] = GPIO.input(self.output_pin)
        return state

    def wait_until_dest_becomes_zero(self, dest, check_interval=0.05):
        """
        Wait until the destination square (dest) becomes stable (0 = piece placed).
        """
        while True:
            current = self.read_sensor_array()
            if current[dest] == 0:
                return current  # Return updated sensor array
            time.sleep(check_interval)

    def detect_move(self, board):
        """
        Continuously checks sensor states until a move is detected.
        Returns a UCI move string (e.g., 'e2e4').
        call detect_move(board) in the main function
        """
        while True:
            if not self.sensors_active:
                time.sleep(0.1)  # Pause sensor detection
                continue
            
            curr_state = self.read_sensor_array()
            
            # Detect if any change occurred
            if curr_state != self.prev_state:
                # Save transient state (for intermediate readings)
                transient_state = curr_state[:]
                time.sleep(0.05)  # Short delay to stabilize readings
                new_curr_state = self.read_sensor_array()
                
                move = self.get_move_from_sensor_states(self.prev_state, transient_state, new_curr_state, board)
                if move:
                    self.prev_state = new_curr_state  # Update previous state after detecting a move
                    return move
            
            time.sleep(0.1)  # Prevent excessive CPU usage
    

    def get_move_from_sensor_states(self, prev_state, transient_state, curr_state, board):
            """
            Using sensor readings, detect a move and return a UCI move string.
            """
            pickup_square = None
            drop_square = None

            # Detect pickup (0 -> 1 transition)
            for i in range(64):
                if prev_state[i] == 0 and curr_state[i] == 1:
                    pickup_square = i
                    break
            if pickup_square is None:
                led_module.clear_leds()
                return None

            led_module.highlight_moves(board, pickup_square)

            # Detect drop location, considering transient state for captures
            for i in range(64):
                if prev_state[i] == 1 and curr_state[i] == 0:
                    drop_square = i
                    break
                elif prev_state[i] == 0 and transient_state[i] == 1:  # Capture case
                    if curr_state[i] != 0:
                        new_state = self.wait_until_dest_becomes_zero(i)
                        curr_state[i] = new_state[i]
                    if curr_state[i] == 0:
                        drop_square = i
                        break
            
            if drop_square is None:
                return None
            
            led_module.update_board_display((pickup_square, drop_square))

            return pickup_square, drop_square
    
    def pause_sensor_detection(self):
        """
        Disables sensor detection temporarily.
        """
        self.sensors_active = False
    
    def resume_sensor_detection(self):
        """
        Enables sensor detection after being paused.
        """
        self.sensors_active = True
    
    def save_current_state_as_previous(self):
        """
        Saves the current state as the previous state, useful for move correction.
        """
        self.prev_state = self.read_sensor_array()

# Cleanup GPIO on exit
def cleanup_gpio():
    GPIO.cleanup()
