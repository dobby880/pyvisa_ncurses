import curses
import time
import threading
import pyvisa
import os
# Define initial values
#USB_PORT='ASRL/dev/ttyUSB3::INSTR'
USB_PORT='USB0::1510::8752::9031683::0::INSTR'
names=['Channel 1', 'Channel 2', 'Channel 3']
toggle_allowed=[True,True,True]
voltage = [0, 0, 0]
current = ['0', '0', '0']
max_current=['0','0','0']
status = [False, False, False]
rm = None
inst = None
device = ''
error_msg = ''
error_counter = 0
connected=False
mutex=threading.Lock()

def connect_usb():
    global device, inst, rm, connected
    print("try to connect ot usb")
    while not connected:
        try:
            with mutex:
                device = "Try to connect to USB"
                rm = pyvisa.ResourceManager()
                inst = rm.open_resource(USB_PORT)
                device = inst.query('*IDN?')
                connected=True
        except:
            print("Error connicting to USB, restart usb port")
            os.system("usbreset 05e6:2230")
            time.sleep(0.1)


# Function to simulate reading voltage and current values
def read_voltage_current():
    global voltage, current, max_current, status, device, connected

    while inst == None or not connected:
        connect_usb()
        print("USB connected")
    while True:
        try:
#            inst = rm.open_resource(USB_PORT)
            with mutex:
                device = inst.query('*IDN?')
                for i in range(len(names)):
                    inst.write(f'INSTRUMENT:SELECT CH{i+1}')
                    voltage[i] = inst.query(f'MEASURE:VOLTAGE?').rstrip() # Example: Replace with actual reading logic
                    current[i] = f"{inst.query(f'MEASURE:CURRENT?').rstrip()}"
                    max_current[i]=f"{inst.query(f'SOURCE:CURRENT?').rstrip()} (+/- {inst.query(f'SOURCE:CURRENT:STEP?').rstrip()})"   # Example: Replace with actual reading logic
                    status[i] = inst.query(f'CHAN:OUTP?').rstrip() # Replace
                    if status[i] == '1' or status[i] == 'ON':
                        status[i] = True
                    elif status[i] == '0' or status[i] == 'OFF':
                        status[i] = False
        except Exception as e:
            print(f"caught annoying error {e}")
#        finally:
#            try:
#                inst.close()
#            except:
#                print('No session to close')
        time.sleep(1)

def change_current_rate(up_down):
    with mutex:
        for i in range(len(names)):
            inst.write(f'INSTRUMENT:SELECT CH{i+1}')
            old_val = float(inst.query(f'SOURCE:CURRENT:STEP?').rstrip())
            new_val = min(max(round(old_val + up_down*0.01,2),0.001),1.0)
            inst.write(f'SOURCE:CURRENT:STEP {new_val}A')
 
def change_current(index, up_down):
    global status, error_msg
    if toggle_allowed[index]:
        try:
            with mutex:
                on_off = int(not status[index])
                inst.write(f'INSTRUMENT:SELECT CH{index+1}')
                inst.write(f'SOURCE:CURRENT:STEP 0.1A')
                if up_down == 1:
                    inst.write(f'SOURCE:CURRENT:UP')
                elif up_down == -1:
                    inst.write(f'SOURCE:CURRENT:DOWN')
        except:
            status[index] = not status[index]
    else:
        error_msg="Toggle not allowed for this Channel"
        status[index] = not status[index]


# Function to handle the on/off toggle action
def toggle_status(index):
    global status, error_msg
    if toggle_allowed[index]:
        try:
#            inst = rm.open_resource(USB_PORT)
            with mutex:
                on_off = int(not status[index])
                inst.write(f'INSTRUMENT:SELECT CH{index+1}')
                inst.write(f'CHANNEL:OUTPUT {on_off}')
#            ret = inst.query(f":OUTPut{index+1}:STATe {on_off}", 3)
        except:
            status[index] = not status[index]
 #       finally:
 #           try:
 #               inst.close()
 #           except:
 #               print('No session to close')
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

    grid_height = 12
    grid_width=40
    starts = []
    def draw_grid():
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        min_cols, min_lines = 120, 20
        try:
            size = os.get_terminal_size()
            if size.columns < min_cols or size.lines < min_lines:
                stdscr.clear()
                stdscr.addstr(0, 0, f"[Error] The terminal winodw is too small. Please increase to {min_cols}x{min_lines}.")
                stdscr.addstr(2, 0, "Press any key to retry...")
                stdscr.refresh()
                stdscr.getch()
                return
        except OSError:
            pass

        stdscr.addstr(0, 1, f'Connected to {device}')
        # Define grid40
        #grid_height = height // 2
#        grid_width = width // 2
        (rows, cols) = (1,3)
        for i in range(rows):
            for j in range(cols):
                # Calculate position
                start_y = 2 + i * grid_height
                start_x = j * grid_width
                starts.append((start_x, start_y))
                # Select color pair based on status
                color_pair = (i * cols + j + 1) % 4 + 1 if status[i * cols + j] else 5

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
                stdscr.addstr(start_y + 1, start_x + 1, f"{names[i*cols+j]}".center(grid_width-2))
                stdscr.addstr(start_y + 3, start_x + 1, f"Channel: {i * cols + 1 + j}")
                stdscr.addstr(start_y + 4, start_x + 1, f"Voltage: {voltage[i * cols + j]}")
                stdscr.addstr(start_y + 5, start_x + 1, f"Current: {current[i * cols + j]}")
                stdscr.addstr(start_y + 6, start_x + 1, f"Max_Cur: {max_current[i * cols + j]}")
                stdscr.addstr(start_y + 7, start_x + 1, f"Status:  {'ON' if status[i * cols + j] else 'OFF'}")
                stdscr.attroff(curses.color_pair(color_pair))
                stdscr.addstr(start_y + 9, start_x + 1, f"Press {chr(ord('1')+i*cols+j)} to toggle ON/OFF".center(grid_width-2))
                stdscr.addstr(start_y + 10, start_x + 1, f"Max_cur: -:F{chr(ord('1')+2*(i*cols+j))}, +:F{chr(ord('2')+2*(i*cols+j))}".center(grid_width-2))

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
       
        stdscr.addstr(start_y+10+i+2, 1, f"Press +/- to increase/decrease the CURRENT stepsize by +/- 0.01")
        stdscr.addstr(start_y+11+i+2, 1, f"Press q to quit")
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
        while device is None:
            time.sleep(.5)
        draw_grid()

        while True:
            key = stdscr.getch()

            if error_msg != '':
                error_message(error_msg)
            if key == ord('q'):
                try:
                    inst.close()
                except:
                    print('Nothing to close')
                break
            elif key == ord('1'):
                confirm_toggle(0)
            elif key == ord('2'):
                confirm_toggle(1)
            elif key == ord('3'):
                confirm_toggle(2)
            elif key == ord('4'):
                confirm_toggle(3)
            elif key == ord('+'):
                change_current_rate(up_down=+1)
            elif key == ord('-'):
                change_current_rate(up_down=-1)
            elif key == curses.KEY_F1:
                change_current(0,-1)
            elif key == curses.KEY_F2:
                change_current(0,+1)
            elif key == curses.KEY_F3:
                change_current(1,-1)
            elif key == curses.KEY_F4:
                change_current(1,+1)
            elif key == curses.KEY_F5:
                change_current(2,-1)
            elif key == curses.KEY_F6:
                change_current(2,+1)
            draw_grid()

    print("Start main loop")
    main_loop()

# Start the thread to read voltage and current values
threading.Thread(target=read_voltage_current, daemon=True).start()

# Run the main function inside the curses wrapper
curses.wrapper(init_screen)
