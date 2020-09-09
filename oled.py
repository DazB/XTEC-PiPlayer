
import smbus
import font

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
DDRAM_top = []
DDRAM_bot = []

################################################################################
# OLED communication functions
################################################################################
def oled_init():
    print('Initalising OLED')
    oled_write_command(0xAE) # Display off
    oled_write_command(0x20) # Set Memory Addressing Mode
    oled_write_command(0x10) # 00,Horizontal Addressing Mode; 01,Vertical Addressing Mode; 10,Page Addressing Mode (RESET); 11,Invalid
    oled_write_command(0x04) # Set low column address
    oled_write_command(0x10) # Set high column address
    oled_write_command(0x40) # Set start line address
    oled_write_command(0xB0) # Set Page Start Address for Page Addressing Mode,0-7
    oled_write_command(0x81) # set contrast control register
    oled_write_command(0xD0) # Default to 50%
    oled_write_command(0xA1) # Set segment re-map 0 to 127
    oled_write_command(0xA6) # Set normal colour
    oled_write_command(0xA8) # Set multiplex ratio(1 to 64)
    oled_write_command(0x1F) # Set multiplex ratio
    oled_write_command(0xAD) # Set charge pump enable
    oled_write_command(0x8B) # Vcc
    oled_write_command(0x30) # Set Vpp
    oled_write_command(0xC8) # Set COM Output Scan Direction
    oled_write_command(0xD3) # Set display vertical offset
    oled_write_command(0x00) # Not offset
    oled_write_command(0xD5) # Set display clock divide ratio/oscillator frequency
    oled_write_command(0x80) # Set divide ratio
    oled_write_command(0xD9) # Set pre-charge period
    oled_write_command(0x22)
    oled_write_command(0xDA) # Set com pins hardware configuration
    oled_write_command(0x02) # 12
    oled_write_command(0xDB) # Set vcomh
    oled_write_command(0x40) # 0x20,0.77xVcc 
    oled_write_command(0xA4) # Output follows RAM content;0xa5,Output ignores RAM content
    oled_write_command(0x8D) # Set DC-DC enable
    oled_write_command(0x14)
    oled_write_command(0xAF) # Turn on panel

def oled_tasks():
    """Main oled task. On each call will iterate and check one character drawn on top 
    and bottom row. If we reach a character and there is a difference to what 
    is shown and what should be shown (e.g. difference in DDRAM or cursor changed) we 
    update what we know is shown on the screen and redraw it on the OLED"""
    global screen_pos

    #  These flags determine whether we will need to redraw a character or 
    #  cursor due to change made by user
    draw_top_flag = False
    draw_bot_flag = False
    draw_top_cursor_flag = False
    draw_bot_cursor_flag = False
    # Increment character position we're drawing
    screen_pos = (screen_pos + 1) % 15

    # if DDRAM_top[screen_pos] != oled_d





def oled_write_command(command):
    """Send a bytes to the control register"""
    i2c_bus.write_byte_data(OLED_I2C_ADDR, 0x00, command)

def oled_write_display(display_list):
    """Send a list of bytes to the display GGDRAM register"""
    i2c_bus.write_i2c_block_data(OLED_I2C_ADDR, 0x40, display_list)

def oled_draw_char(char_data, char_pos):
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
        oled_write_command(page)
        oled_write_command(start_col & 0b1111) # FIXME: is this right?
        oled_write_command(0x10 + (start_col >> 4))

        character_data_list = []
        
        # Put character data into a list
        for _ in range(0, 8, 1):
            character_data_list.append(char_data[char_index])
            char_index = char_index + 2

        # Send character data to OLED
        oled_write_display(character_data_list)
        char_index = 2  # Move to lower 8 bytes of font
        page += 1


################################################################################
# Virutal DDRAM functions
# Functions to interact with the display RAM
################################################################################
 
def oled_write_char_DDRAM(ch):
    """Write 1 char to the current DDRAM location then increment DDRAM position"""
    global DDRAM_pos
    # Below 28h put in top row RAM
    if DDRAM_pos < 0x28:
        DDRAM_top[DDRAM_pos] = ch
    # Otherwise put in bottom row RAM
    else:
        DDRAM_bot[DDRAM_pos - 0x40] = ch

    DDRAM_pos += 1

def oled_write_string_DDRAM(str):
    """Calls oled_write_char_DDRAM multiple times for entire string"""
    for char in str:
        oled_write_char_DDRAM(char)

def oled_clear_DDRAM():
    """Clears DDRAM by setting each element in DDRAM to space character"""
    for i in range(0, DDRAM_LINE_SIZE, 1):
        DDRAM_top[i] = 0x20
        DDRAM_bot[i] = 0x20

def oled_set_DDRAM_addr(address):
    """Sets DDRAM address (character position to next write to)"""
    global DDRAM_pos
    DDRAM_pos = address

# Main entry point.
if __name__ == '__main__':
    oled_init()
    oled_clear_DDRAM()
    oled_draw_char([0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x33, 0xFF, 0x33, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 1)
    print('Done')
