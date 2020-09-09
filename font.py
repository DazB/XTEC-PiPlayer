CHAR_ROW_SIZE = 17 # Size of one character stored in CGROM or CGRAM

# Standard font, 8 x 15 pixels
CGROM = [ 
        0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char SPACE 
        0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x33, 0xFF, 0x33, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char !
        0x07, 0x00, 0x00, 0x1E, 0x00, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x1E, 0x00, 0x00, 0x00,  # Code for char "
        0x07, 0x30, 0x03, 0xFE, 0x1F, 0xFE, 0x1F, 0x30, 0x03, 0xFE, 0x1F, 0xFE, 0x1F, 0x30, 0x03, 0x00, 0x00,  # Code for char #
        0x07, 0x7C, 0x0C, 0xC6, 0x18, 0xC6, 0x18, 0xFF, 0x3F, 0xC6, 0x18, 0xC6, 0x18, 0x8C, 0x0F, 0x00, 0x00,  # Code for char $
        0x07, 0x0C, 0x30, 0x12, 0x1C, 0x0C, 0x07, 0xC0, 0x01, 0x70, 0x18, 0x1C, 0x24, 0x06, 0x18, 0x00, 0x00,  # Code for char %
        0x07, 0x1E, 0x0F, 0xBF, 0x1F, 0xE3, 0x18, 0xE3, 0x18, 0xBF, 0x0F, 0x1E, 0x1F, 0x80, 0x19, 0x00, 0x00,  # Code for char &
        0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x17, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char '
        0x06, 0x00, 0x00, 0xE0, 0x03, 0xF8, 0x0F, 0x1C, 0x1C, 0x06, 0x30, 0x03, 0x60, 0x00, 0x00, 0x00, 0x00,  # Code for char (
        0x06, 0x00, 0x00, 0x03, 0x60, 0x06, 0x30, 0x1C, 0x1C, 0xF8, 0x0F, 0xE0, 0x03, 0x00, 0x00, 0x00, 0x00,  # Code for char )
        0x07, 0x48, 0x02, 0x50, 0x01, 0xE0, 0x00, 0xFC, 0x07, 0xE0, 0x00, 0x50, 0x01, 0x48, 0x02, 0x00, 0x00,  # Code for char *
        0x07, 0x00, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xF0, 0x03, 0xF0, 0x03, 0xC0, 0x00, 0xC0, 0x00, 0x00, 0x00,  # Code for char +
        0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x70, 0x00, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char ,
        0x07, 0x00, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0x00, 0x00,  # Code for char -
        0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x00, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char .
        0x07, 0x00, 0x70, 0x00, 0x3C, 0x00, 0x0F, 0xC0, 0x03, 0xF0, 0x00, 0x3C, 0x00, 0x0F, 0x00, 0x00, 0x00,  # Code for char /
        0x07, 0xFE, 0x1F, 0xFF, 0x3F, 0x83, 0x31, 0xC3, 0x30, 0x63, 0x30, 0xFF, 0x3F, 0xFE, 0x1F, 0x00, 0x00,  # Code for char 0
        0x07, 0x08, 0x30, 0x0C, 0x30, 0x06, 0x30, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x30, 0x00, 0x30, 0x00, 0x00,  # Code for char 1
        0x07, 0x86, 0x3F, 0xC7, 0x3F, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xFF, 0x30, 0x7E, 0x30, 0x00, 0x00,  # Code for char 2
        0x07, 0x06, 0x18, 0x07, 0x38, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xFF, 0x3F, 0x3E, 0x1F, 0x00, 0x00,  # Code for char 3
        0x07, 0xFF, 0x00, 0xFF, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x00,  # Code for char 4
        0x07, 0xFF, 0x30, 0xFF, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x3F, 0x83, 0x1F, 0x00, 0x00,  # Code for char 5
        0x07, 0xFE, 0x1F, 0xFF, 0x3F, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xC7, 0x3F, 0x86, 0x1F, 0x00, 0x00,  # Code for char 6
        0x07, 0x07, 0x30, 0x03, 0x3C, 0x03, 0x0F, 0xC3, 0x03, 0xF3, 0x00, 0x3F, 0x00, 0x0F, 0x00, 0x00, 0x00,  # Code for char 7
        0x07, 0x3E, 0x1F, 0xFF, 0x3F, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xFF, 0x3F, 0x3E, 0x1F, 0x00, 0x00,  # Code for char 8
        0x07, 0x7E, 0x18, 0xFF, 0x38, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xFF, 0x3F, 0xFE, 0x1F, 0x00, 0x00,  # Code for char 9
        0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x70, 0x0E, 0x70, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char :
        0x04, 0x00, 0x00, 0x00, 0x30, 0x70, 0x1E, 0x70, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Code for char ;
        0x07, 0x40, 0x00, 0xE0, 0x00, 0xB0, 0x01, 0x18, 0x03, 0x0C, 0x06, 0x06, 0x0C, 0x03, 0x18, 0x00, 0x00,  # Code for char <
        0x07, 0x00, 0x00, 0x60, 0x06, 0x60, 0x06, 0x60, 0x06, 0x60, 0x06, 0x60, 0x06, 0x60, 0x06, 0x00, 0x00,  # Code for char =
        0x08, 0x00, 0x00, 0x03, 0x18, 0x06, 0x0C, 0x0C, 0x06, 0x18, 0x03, 0xB0, 0x01, 0xE0, 0x00, 0x40, 0x00,  # Code for char >
        0x07, 0x06, 0x00, 0x07, 0x00, 0x03, 0x00, 0x83, 0x37, 0xC3, 0x37, 0xFF, 0x00, 0x7E, 0x00, 0x00, 0x00,  # Code for char ?
        0x07, 0xFE, 0x1F, 0xFF, 0x3F, 0x03, 0x30, 0xF3, 0x31, 0x93, 0x31, 0xFF, 0x39, 0xFE, 0x19, 0x00, 0x00,  # Code for char @
        0x07, 0xFE, 0x3F, 0xFF, 0x3F, 0xC3, 0x00, 0xC3, 0x00, 0xC3, 0x00, 0xFF, 0x3F, 0xFE, 0x3F, 0x00, 0x00,  # Code for char A
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xFF, 0x3F, 0x3E, 0x1F, 0x00, 0x00,  # Code for char B
        0x07, 0xFE, 0x1F, 0xFF, 0x3F, 0x03, 0x30, 0x03, 0x30, 0x03, 0x30, 0x0F, 0x3C, 0x0E, 0x1C, 0x00, 0x00,  # Code for char C
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0x03, 0x30, 0x03, 0x30, 0x07, 0x38, 0xFE, 0x1F, 0xFC, 0x0F, 0x00, 0x00,  # Code for char D
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0x03, 0x30, 0x00, 0x00,  # Code for char E
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0xC3, 0x00, 0xC3, 0x00, 0xC3, 0x00, 0xC3, 0x00, 0x03, 0x00, 0x00, 0x00,  # Code for char F
        0x07, 0xFE, 0x1F, 0xFF, 0x3F, 0x03, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xC7, 0x3F, 0xC6, 0x1F, 0x00, 0x00,  # Code for char G
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x00,  # Code for char H
        0x07, 0x03, 0x30, 0x03, 0x30, 0xFF, 0x3F, 0xFF, 0x3F, 0x03, 0x30, 0x03, 0x30, 0x03, 0x30, 0x00, 0x00,  # Code for char I
        0x07, 0x00, 0x18, 0x00, 0x38, 0x03, 0x30, 0x03, 0x30, 0xFF, 0x3F, 0xFF, 0x1F, 0x03, 0x00, 0x00, 0x00,  # Code for char J
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0x30, 0x03, 0x18, 0x06, 0x0C, 0x0C, 0x06, 0x18, 0x03, 0x30, 0x00, 0x00,  # Code for char K
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x00,  # Code for char L
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0x0C, 0x00, 0x38, 0x00, 0x0C, 0x00, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x00,  # Code for char M
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0x18, 0x00, 0x60, 0x00, 0x80, 0x01, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x00,  # Code for char N
        0x07, 0xFE, 0x1F, 0xFF, 0x3F, 0x03, 0x30, 0x03, 0x30, 0x03, 0x30, 0xFF, 0x3F, 0xFE, 0x1F, 0x00, 0x00,  # Code for char O
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0xC3, 0x00, 0xC3, 0x00, 0xC3, 0x00, 0xFF, 0x00, 0x7E, 0x00, 0x00, 0x00,  # Code for char P
        0x07, 0xFE, 0x0F, 0xFF, 0x1F, 0x03, 0x18, 0x03, 0x1C, 0x03, 0x1C, 0xFF, 0x3F, 0xFE, 0x33, 0x00, 0x00,  # Code for char Q
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0xC3, 0x03, 0xC3, 0x07, 0xC3, 0x0E, 0xFF, 0x1C, 0x7E, 0x38, 0x00, 0x00,  # Code for char R
        0x07, 0x7E, 0x1C, 0xFF, 0x3C, 0xC3, 0x30, 0xC3, 0x30, 0xC3, 0x30, 0xCF, 0x3F, 0x8E, 0x1F, 0x00, 0x00,  # Code for char S
        0x07, 0x03, 0x00, 0x03, 0x00, 0xFF, 0x3F, 0xFF, 0x3F, 0x03, 0x00, 0x03, 0x00, 0x03, 0x00, 0x00, 0x00,  # Code for char T
        0x07, 0xFF, 0x1F, 0xFF, 0x3F, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0xFF, 0x3F, 0xFF, 0x1F, 0x00, 0x00,  # Code for char U
        0x07, 0xFF, 0x01, 0xFF, 0x1F, 0x00, 0x3E, 0x00, 0x30, 0x00, 0x3E, 0xFF, 0x1F, 0xFF, 0x01, 0x00, 0x00,  # Code for char V
        0x07, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x0C, 0x00, 0x07, 0x00, 0x0C, 0xFF, 0x3F, 0xFF, 0x3F, 0x00, 0x00,  # Code for char W
        0x07, 0x0F, 0x3C, 0x3E, 0x1E, 0x70, 0x07, 0xC0, 0x01, 0x70, 0x07, 0x3E, 0x1E, 0x0F, 0x3C, 0x00, 0x00,  # Code for char X
        0x07, 0x07, 0x00, 0x3E, 0x00, 0x78, 0x00, 0xE0, 0x3F, 0xF8, 0x3F, 0x7E, 0x00, 0x0F, 0x00, 0x00, 0x00,  # Code for char Y
        0x07, 0x03, 0x38, 0x03, 0x3E, 0x83, 0x37, 0xE3, 0x31, 0x7B, 0x30, 0x1F, 0x30, 0x07, 0x30, 0x00, 0x00,  # Code for char Z
]

BLINK_BLOCK = [0x05, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00]    # Code for big old block
CURSOR = [0x05, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0x00]         # Code for cursor line
