//! Constants used throughout the attpc_conduit backend
// Data sizes and types
pub const EXPECTED_META_TYPE: u8 = 8;
pub const EXPECTED_HEADER_SIZE: u16 = 1;
pub const EXPECTED_ITEM_SIZE_PARTIAL: u16 = 4;
pub const EXPECTED_ITEM_SIZE_FULL: u16 = 2;
pub const EXPECTED_FRAME_TYPE_PARTIAL: u16 = 1;
pub const EXPECTED_FRAME_TYPE_FULL: u16 = 2;
pub const SIZE_UNIT: u32 = 256;
#[allow(dead_code)]
pub const SIZE_OF_BITSET: usize = 72;

// Electronics constants
pub const NUMBER_OF_COBOS: u8 = 11; //total
pub const COBO_WITH_TIMESTAMP: u8 = 10; // cobo with TS in sync with FRIBDAQ
#[allow(dead_code)]
pub const NUMBER_OF_ASADS: u8 = 4; //per cobo
pub const NUMBER_OF_AGETS: u8 = 4; // per asad
pub const NUMBER_OF_CHANNELS: u8 = 68;
pub const NUMBER_OF_TIME_BUCKETS: u32 = 512;
pub const NUMBER_OF_MATRIX_COLUMNS: usize = NUMBER_OF_TIME_BUCKETS as usize + 5; // cobo, asad, aget, channel, pad, buckets

// GETDAQ constants
pub const MM_IP_SUBNET: &str = "192.168.41"; // Subnet for all the MacMini's in AT-TPC
pub const EXPORTER_PORT: &str = "46491"; // This maybe should be exposed? idk
