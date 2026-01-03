//                            USER DEFINED SETTINGS
//   Set driver type, fonts to be loaded, pins used and SPI control method etc.
//
//   See the User_Setup_Select.h file if you wish to be able to define multiple
//   setups and then easily select which setup file is used by the compiler.
//
//   If this file is edited correctly then all the library example sketches should
//   run without the need to make any more changes for a particular hardware setup!
//   Note that some sketches are designed for a particular TFT pixel width/height

// User defined information reported by "Read_User_Setup" test & diagnostics example
#define USER_SETUP_INFO "User_Setup"
#define USER_SETUP_LOADED 1

#define GC9A01_DRIVER

// Set display size
#define TFT_WIDTH  240
#define TFT_HEIGHT 240

// Pin definitions
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS    5
#define TFT_DC    2
#define TFT_RST   4
// #define TFT_BL   15

// Optional: SPI frequency (40MHz works well)
#define SPI_FREQUENCY 40000000


#define LOAD_GLCD   // Font 1
// #define LOAD_FONT2  // Font 2
// #define LOAD_FONT4  // Font 4
// #define LOAD_FONT6  // Font 6
// #define LOAD_FONT7  // Font 7
// #define LOAD_FONT8  // Font 8
// #define LOAD_GFXFF 