
import smbus
import font
from threading import Timer

################################################################################
# Global variables
################################################################################
# OLED i2c address
OLED_I2C_ADDR = 0x3C
# i2c bus
i2c_bus = smbus.SMBus(0)

DDRAM_LINE_SIZE = 40
OLED_DISPLAY_LINE_SIZE = 16

# OLED information
DDRAM_pos = 0
cursor_enabled = False
cursor_showing = False
blinking_enabled = False
blinking_showing = False
screen_pos = 0

# DDRAM is our display buffer
DDRAM_top = [None] * DDRAM_LINE_SIZE
DDRAM_bot = [None] * DDRAM_LINE_SIZE

class OledDisplayData():
    """Object storing oled display data information"""
    def __init__(self, char_displayed, cursor_displayed):
        self.char_displayed = char_displayed
        self.cursor_displayed = cursor_displayed

# OLED display is what is actually currently shown on OLED
OLED_display_top = [OledDisplayData(None, False) for _ in range(DDRAM_LINE_SIZE)]
OLED_display_bot = [OledDisplayData(None, False) for _ in range(DDRAM_LINE_SIZE)]

oled_cursor_timer = None

################################################################################
# OLED communication functions
################################################################################
def init():
    """OLED intialisation functions. Sends startup data to OLED"""
    global oled_cursor_timer

    print('Initalising OLED')
    clear_DDRAM()

    write_command(0xAE) # Display off
    write_command(0x20) # Set Memory Addressing Mode
    write_command(0x10) # 00,Horizontal Addressing Mode; 01,Vertical Addressing Mode; 10,Page Addressing Mode (RESET); 11,Invalid
    write_command(0x04) # Set low column address
    write_command(0x10) # Set high column address
    write_command(0x40) # Set start line address
    write_command(0xB0) # Set Page Start Address for Page Addressing Mode,0-7
    write_command(0x81) # set contrast control register
    write_command(0xD0) # Default to 50%
    write_command(0xA1) # Set segment re-map 0 to 127
    write_command(0xA6) # Set normal colour
    write_command(0xA8) # Set multiplex ratio(1 to 64)
    write_command(0x1F) # Set multiplex ratio
    write_command(0xAD) # Set charge pump enable
    write_command(0x8B) # Vcc
    write_command(0x30) # Set Vpp
    write_command(0xC8) # Set COM Output Scan Direction
    write_command(0xD3) # Set display vertical offset
    write_command(0x00) # Not offset
    write_command(0xD5) # Set display clock divide ratio/oscillator frequency
    write_command(0x80) # Set divide ratio
    write_command(0xD9) # Set pre-charge period
    write_command(0x22)
    write_command(0xDA) # Set com pins hardware configuration
    write_command(0x02) # 12
    write_command(0xDB) # Set vcomh
    write_command(0x40) # 0x20,0.77xVcc 
    write_command(0xA4) # Output follows RAM content;0xa5,Output ignores RAM content
    write_command(0x8D) # Set DC-DC enable
    write_command(0x14)
    write_command(0xAF) # Turn on panel

    # Start cursor timer callback
    oled_cursor_timer = Timer(0.3, cursor_callback)
    oled_cursor_timer.daemon = True
    oled_cursor_timer.start()

def tasks():
    """Main oled task. On each call will iterate and check one character drawn on top 
    and bottom row. If we reach a character and there is a difference to what 
    is shown and what should be shown (e.g. difference in DDRAM or cursor changed) we 
    update what we know is shown on the screen and redraw it on the OLED"""
    global screen_pos, DDRAM_top, OLED_display_top, DDRAM_bot, OLED_display_bot
    
    #  These flags determine whether we will need to redraw a character or 
    #  cursor due to change made by user
    draw_top_flag = False
    draw_bot_flag = False
    draw_top_cursor_flag = False
    draw_bot_cursor_flag = False
    # Increment character position we're drawing
    screen_pos = (screen_pos + 1) % OLED_DISPLAY_LINE_SIZE

    # If there is a different character on screen to the one stored in DDRAM
    if DDRAM_top[screen_pos] != OLED_display_top[screen_pos].char_displayed:
        OLED_display_top[screen_pos].char_displayed = DDRAM_top[screen_pos]
        draw_top_flag = True

    # If the cursor is showing and it shouldn't be on this character
    if OLED_display_top[screen_pos].cursor_displayed and ((screen_pos != DDRAM_pos) or 
        ((screen_pos == DDRAM_pos) and ((not blinking_showing and blinking_enabled) or (not cursor_showing and cursor_enabled)))):
        OLED_display_top[screen_pos].cursor_displayed = False
        draw_top_flag = True
    # Else if the cursor is not showing and it should be on this character
    elif not OLED_display_top[screen_pos].cursor_displayed and (screen_pos == DDRAM_pos) and (blinking_showing or cursor_showing):
        OLED_display_top[screen_pos].cursor_displayed = True
        draw_top_flag = True
        draw_top_cursor_flag = True

    # Now do all the same again but with the bottom characters
    # ???TODO: maybe there's a better way to do this instead of repeating the code?
    
    # If there is a different character on screen to the one stored in DDRAM   
    if DDRAM_bot[screen_pos] != OLED_display_bot[screen_pos].char_displayed:
        OLED_display_bot[screen_pos].char_displayed = DDRAM_bot[screen_pos]
        draw_bot_flag = True

    # If the cursor is showing and it shouldn't be on this character
    if OLED_display_bot[screen_pos].cursor_displayed and ((screen_pos != DDRAM_pos - 0x40) or 
        ((screen_pos == DDRAM_pos - 0x40) and ((not blinking_showing and blinking_enabled) or (not cursor_showing and cursor_enabled)))):
        OLED_display_bot[screen_pos].cursor_displayed = False
        draw_bot_flag = True
    # Else if the cursor is not showing and it should be on this character
    elif not OLED_display_bot[screen_pos].cursor_displayed and (screen_pos == DDRAM_pos - 0x40) and (blinking_showing or cursor_showing):
        OLED_display_bot[screen_pos].cursor_displayed = True
        draw_bot_flag = True
        draw_bot_cursor_flag = True

    # Check flags and determine whether we draw to the screen
    if draw_top_flag:
        # We are drawing a top row character
        draw_top_flag = False
        
        # Data array for single character being displayed
        font_pos = (ord(DDRAM_top[screen_pos]) - 32) * font.CHAR_ROW_SIZE
        top_row_char_data = font.CGROM[font_pos : (font_pos + font.CHAR_ROW_SIZE)]

        # If we're drawing a cursor
        if draw_top_cursor_flag:
            draw_top_cursor_flag = False

            # If we're drawing the blinking block
            if blinking_showing:
                # OR the character data we're going to draw with the block data
                for i in range(0, font.CHAR_ROW_SIZE):
                    top_row_char_data[i] |= font.BLINK_BLOCK[i]
            # Else if we're drawing the cursor line
            elif cursor_showing:
                # OR the character data we're going to draw with the cursor data
                for i in range(0, font.CHAR_ROW_SIZE):
                    top_row_char_data[i] |= font.CURSOR[i]
        # Draw the resulting character
        draw_char(top_row_char_data, screen_pos)   # Top row character

    # Same as above
    if draw_bot_flag:
        # We are drawing a top row character
        draw_bot_flag = False
        
        # Data array for single character being displayed
        font_pos = (ord(DDRAM_bot[screen_pos]) - 32) * font.CHAR_ROW_SIZE
        bot_row_char_data = font.CGROM[font_pos : (font_pos + font.CHAR_ROW_SIZE)]

        # If we're drawing a cursor
        if draw_bot_cursor_flag:
            draw_bot_cursor_flag = False

            # If we're drawing the blinking block
            if blinking_showing:
                # OR the character data we're going to draw with the block data
                for i in range(0, font.CHAR_ROW_SIZE):
                    bot_row_char_data[i] |= font.BLINK_BLOCK[i]
            # Else if we're drawing the cursor line
            elif cursor_showing:
                # OR the character data we're going to draw with the cursor data
                for i in range(0, font.CHAR_ROW_SIZE):
                    bot_row_char_data[i] |= font.CURSOR[i]
        # Draw the resulting character
        draw_char(bot_row_char_data, screen_pos + 0x40)    # Bottom row character


def write_command(command):
    """Send a bytes to the control register"""
    global i2c_bus
    i2c_bus.write_byte_data(OLED_I2C_ADDR, 0x00, command)

def write_display(display_list):
    """Send a list of bytes to the display GGDRAM register"""
    global i2c_bus
    i2c_bus.write_i2c_block_data(OLED_I2C_ADDR, 0x40, display_list)

def draw_char(char_data, char_pos):
    """ Takes array of character data, and position to draw on OLED screen,
    and draws data"""
    char_index = 1
    page = 0x00
    start_col = 0

    # If we're printing to top row of screen
    if char_pos < 0x10:
        page = 0xB0                 # Drawing at top of display
        start_col = char_pos * 8    # Start column. All fonts are 8 pixels wide

    else:
        page = 0xB2                         # Drawing at bottom of display
        start_col = (char_pos - 0x40) * 8   # Start column. All fonts are 8 pixels wide
    
    for _ in range(0, 2, 1):
        write_command(page)
        write_command(start_col & 0b1111)
        write_command(0x10 + (start_col >> 4))

        character_data_list = []
        
        # Put character data into a list
        for _ in range(0, 8, 1):
            character_data_list.append(char_data[char_index])
            char_index = char_index + 2

        # Send character data to OLED
        write_display(character_data_list)
        char_index = 2  # Move to lower 8 bytes of font
        page += 1


def cursor_callback():
    """Cursor blink callback timer"""
    global oled_cursor_timer, blinking_enabled, blinking_showing, cursor_enabled, cursor_showing
    if blinking_enabled:
        blinking_showing = not blinking_showing
    if cursor_enabled:
        cursor_showing = not cursor_showing
    # Restart timer
    oled_cursor_timer = Timer(0.3, cursor_callback)
    oled_cursor_timer.daemon = True
    oled_cursor_timer.start()


################################################################################
# Virutal DDRAM functions
# Functions to interact with the display RAM
################################################################################
 
def write_char_DDRAM(ch):
    """Write 1 char to the current DDRAM location then increment DDRAM position"""
    global DDRAM_pos, DDRAM_top, DDRAM_bot
    # Below 28h put in top row RAM
    if DDRAM_pos < 0x28:
        DDRAM_top[DDRAM_pos] = ch
    # Otherwise put in bottom row RAM
    else:
        DDRAM_bot[DDRAM_pos - 0x40] = ch

    DDRAM_pos += 1

def write_string_DDRAM(str):
    """Calls write_char_DDRAM multiple times for entire string"""
    for char in str:
        write_char_DDRAM(char)

def clear_DDRAM():
    """Clears DDRAM by setting each element in DDRAM to space character"""
    global DDRAM_top, DDRAM_bot
    for i in range(0, DDRAM_LINE_SIZE, 1):
        DDRAM_top[i] = chr(0x20)
        DDRAM_bot[i] = chr(0x20)

def clear_top_DDRAM():
    """Clears top row of DDRAM by setting each element in DDRAM to space character"""
    global DDRAM_top
    for i in range(0, DDRAM_LINE_SIZE, 1):
        DDRAM_top[i] = chr(0x20)

def clear_bot_DDRAM():
    """Clears bottom row of DDRAM by setting each element in DDRAM to space character"""
    global DDRAM_bot
    for i in range(0, DDRAM_LINE_SIZE, 1):
        DDRAM_bot[i] = chr(0x20)

def set_DDRAM_addr(address):
    """Sets DDRAM address (character position to next write to)"""
    global DDRAM_pos
    DDRAM_pos = address

def boot():
    """Called once in app startup"""
    init()
    set_DDRAM_addr(0x00)
    boot_message = 'MP2'
    write_string_DDRAM(boot_message)
    set_DDRAM_addr(0x40)
    boot_message = 'BOOTING...'
    write_string_DDRAM(boot_message)
    # Do tasks enough times to just write boot message
    for _ in range(0, OLED_DISPLAY_LINE_SIZE + 1, 1):
        tasks()
