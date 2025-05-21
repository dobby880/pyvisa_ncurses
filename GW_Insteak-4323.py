import curses
import time
import threading
import pyvisa

# Define initial values
USB_PORT='ASRL/dev/ttyUSB3::INSTR'
names = ['DOrbit SDK','Flight Model', '', 'Engineering Model']
toggle_allowed=[True,True,False,True]
voltage = [0, 0, 0, 0]
current = ['0', '0', '0', '0']
status = [False, False, False, False]
rm = pyvisa.ResourceManager()
inst = rm.open_resource(USB_PORT)
device = ''
error_msg = ''
error_counter = 0

# Function to simulate reading voltage and current values
def read_voltage_current():
    global voltage, current, status, device
    while True:
        try:
            device = inst.query('*IDN?')
            for i in range(4):
                voltage[i] = inst.query(f'VOUT{i+1}?').rstrip() # Example: Replace with actual reading logic
                current[i] = inst.query(f'IOUT{i+1}?').rstrip()   # Example: Replace with actual reading logic
                status[i] = inst.query(f':OUTPut{i+1}:STATe?').rstrip() # Replace
                if status[i] == 'ON':
                    status[i] = True
                elif status[i] == 'OFF':
                    status[i] = False
        except:
            print("caught annoying error")
        time.sleep(1)

# Function to handle the on/off toggle action
def toggle_status(index):
    global status, error_msg
    if toggle_allowed[index]:
        try:
            on_off = int(not status[index])
            ret = inst.query(f":OUTPut{index+1}:STATe {on_off}", 3)
        except:
            status[index] = not status[index]
    else:
        error_msg="Toggle not allowed for this Channel"
        status[index] = not status[index]
    # Example: Add actual logic to handle the toggle action

# Initialize the screen
def init_screen(stdscr):
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.timeout(2000)

    # Define colors
    curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Transparent color for OFF state
    curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)  # RED for important stuff

    grid_height = 10
    grid_width=40
    starts = []
    def draw_grid():
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(0, 1, f'Connected to {device}')
        # Define grid40
        #grid_height = height // 2
#        grid_width = width // 2
        for i in range(2):
            for j in range(2):
                # Calculate position
                start_y = 2 + i * grid_height
                start_x = j * grid_width
                starts.append((start_x, start_y))
                # Select color pair based on status
                color_pair = (i * 2 + j + 1) % 4 + 1 if status[i * 2 + j] else 5

                # Draw border
                stdscr.attron(curses.color_pair(color_pair))
                for y in range(start_y, start_y + grid_height):
                    stdscr.addch(y, start_x, '|')
                    stdscr.addch(y, start_x + grid_width - 1, '|')
                for x in range(start_x, start_x + grid_width):
                    if x == start_x or x == start_x+grid_width-1:
                        stdscr.addch(start_y, x, '+')
                        stdscr.addch(start_y + grid_height - 1, x, '+')
                    else:
                        stdscr.addch(start_y, x, '-')
                        stdscr.addch(start_y + grid_height - 1, x, '-')

                # Display values and status
                stdscr.addstr(start_y + 1, start_x + 1, f"{names[i*2+j]}".center(grid_width-2))
                stdscr.addstr(start_y + 3, start_x + 1, f"Channel: {i * 2 + 1 + j}")
                stdscr.addstr(start_y + 4, start_x + 1, f"Voltage: {voltage[i * 2 + j]}")
                stdscr.addstr(start_y + 5, start_x + 1, f"Current: {current[i * 2 + j]}")
                stdscr.addstr(start_y + 6, start_x + 1, f"Status:  {'ON' if status[i * 2 + j] else 'OFF'}")
                stdscr.attroff(curses.color_pair(color_pair))
                stdscr.addstr(start_y + 8, start_x + 1, f"Press {chr(ord('1')+i*2+j)} to toggle ON/OFF".center(grid_width-2))

#        start_y = grid_height*2+2
#        stdscr.addstr(start_y, 1, f"Available Resources:")
#        devices = rm.list_resources()
#        for i in range(len(devices)):
#            key = chr(97+i)
#            dev = devices[i]
#            resources[key] = dev
#            if connected_device[0] == key:
#                stdscr.attron(curses.color_pair(6))
#                stdscr.addstr(start_y+i, 1, f"({key}): {dev} (connected)")
#                stdscr.attroff(curses.color_pair(6))
#            else:
#                stdscr.addstr(start_y+i, 1, f"({key}): {dev}")
       
        stdscr.addstr(start_y+8+i+2, 1, f"Press q to quit")
        stdscr.refresh()

    def error_message(text):
        global error_msg

        height, width = stdscr.getmaxyx()

        line_length = int(width/2)
        lines = []
        for i in range(0, len(text), line_length):
            lines.append(text[i:i+line_length] + '\n')
        x_start = int((20-len(lines))/2)
        y_start = int((width-line_length)/2)

        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(x_start, y_start, '-'*(line_length+4))
        for i in range(len(lines)):
            stdscr.addstr(x_start+i+1, y_start, "  "+lines[i]+"  ")
        stdscr.addstr(x_start+i+2, y_start, '-'*(line_length+4))
        stdscr.attroff(curses.color_pair(6))
        stdscr.refresh()
        time.sleep(3)
        error_msg = ""

    def confirm_toggle(index):
        height, width = stdscr.getmaxyx()
        start_y = starts[index][1]+3
        start_x = starts[index][0]+1
        confirm_msg = f"Are you sure you want POWER {'ON' if not status[index] else 'OFF'} CHANNEL {index+1} {names[index]}?\n(y/n)"
        line_length = grid_width-4
        lines = []
        for line in confirm_msg.split('\n'):
            for i in range(0, len(line), line_length-2):
                lines.append(line[i:i+line_length-2])
 
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(start_y, start_x, '+'+'-'*(line_length)+'+')
        for i in range(len(lines)):
            stdscr.addstr(start_y+i+1, start_x, '|'+f"{lines[i]}".center(line_length)+'|')
        stdscr.addstr(start_y+i+2, start_x, '+'+'-'*(line_length)+'+')
        stdscr.attroff(curses.color_pair(6))
        stdscr.refresh()

        while True:
            key = stdscr.getch()
            if key == ord('y'):
                toggle_status(index)
                break
            elif key == ord('n'):
                break

    def main_loop():
        draw_grid()

        while True:
            key = stdscr.getch()

            if error_msg != '':
                error_message(error_msg)
            if key == ord('q'):
                inst.close()
                break
            elif key == ord('1'):
                confirm_toggle(0)
            elif key == ord('2'):
                confirm_toggle(1)
            elif key == ord('3'):
                confirm_toggle(2)
            elif key == ord('4'):
                confirm_toggle(3)
            draw_grid()

    main_loop()

# Start the thread to read voltage and current values
threading.Thread(target=read_voltage_current, daemon=True).start()

# Run the main function inside the curses wrapper
curses.wrapper(init_screen)
