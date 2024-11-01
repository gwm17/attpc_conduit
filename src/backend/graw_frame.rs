use bitvec::prelude::*;
use byteorder::{BigEndian, ReadBytesExt};
use std::io::Cursor;

use super::constants::*;
use super::error::{GrawDataError, GrawFrameError};

/// Data from a single time-bucket (sampled point along the waveform)
#[derive(Debug, Clone)]
pub struct GrawData {
    pub aget_id: u8,
    pub channel: u8,
    pub time_bucket_id: u16,
    pub sample: i16,
}

impl Default for GrawData {
    fn default() -> Self {
        GrawData {
            aget_id: 0,
            channel: 0,
            time_bucket_id: 0,
            sample: 0,
        }
    }
}

impl GrawData {
    /// Sanity checks
    pub fn check_data(&self) -> Result<(), GrawDataError> {
        if self.aget_id > NUMBER_OF_AGETS {
            return Err(GrawDataError::BadAgetID(self.aget_id));
        }
        if self.channel > NUMBER_OF_CHANNELS {
            return Err(GrawDataError::BadChannel(self.channel));
        }
        if (self.time_bucket_id as u32) > NUMBER_OF_TIME_BUCKETS {
            return Err(GrawDataError::BadTimeBucket(self.time_bucket_id));
        }

        Ok(())
    }
}

#[allow(dead_code)]
fn parse_bitsets(cursor: &mut Cursor<Vec<u8>>) -> Result<Vec<BitVec<u8>>, GrawFrameError> {
    let mut sets: Vec<BitVec<u8>> = Vec::with_capacity(4);
    let mut storage_index: usize;
    let mut byte: u8;
    for _ in 0..4 {
        let mut aget_bits = bitvec![u8, Lsb0; 0; SIZE_OF_BITSET];
        for index in (0..9).rev() {
            storage_index = 8 - index;
            byte = cursor.read_u8()?;
            aget_bits[storage_index..(storage_index + 8)].store(byte);
        }
        sets.push(aget_bits);
    }

    return Ok(sets);
}

#[allow(dead_code)]
fn parse_multiplicity(cursor: &mut Cursor<Vec<u8>>) -> Result<Vec<u16>, GrawFrameError> {
    let mut mults: Vec<u16> = Vec::with_capacity(4);
    let mut mult: u16;
    for _ in 0..4 {
        mult = cursor.read_u16::<BigEndian>()?;
        mults.push(mult);
    }

    return Ok(mults);
}

/// FrameMetadata provides the GrawFile a way of querying the event (hardware-level)
/// information without accessing the entire frame
#[derive(Debug, Clone, Default, PartialEq)]
pub struct FrameMetadata {
    pub event_id: u32,
    pub event_time: u64,
}

impl From<GrawFrameHeader> for FrameMetadata {
    /// Extract metadata from the header
    fn from(value: GrawFrameHeader) -> Self {
        FrameMetadata {
            event_id: value.event_id,
            event_time: value.event_time,
        }
    }
}

/// GrawFrameHeaders contain the full metadata description of the GrawFrame. They are most commonly used to
/// know how large the total frame size is
#[derive(Debug, Clone, Default)]
pub struct GrawFrameHeader {
    pub meta_type: u8,   //set to 0x6 ?
    pub frame_size: u32, //in 256-bit words. Note that this can have some padding at the end
    pub data_source: u8,
    pub frame_type: u16,
    pub revision: u8,
    pub header_size: u16,
    pub item_size: u16,
    pub n_items: u32,
    pub event_time: u64,
    pub event_id: u32,
    pub cobo_id: u8,
    pub asad_id: u8,
    pub read_offset: u16,
    pub status: u8,
    pub total_size_precise: u64, //Actual size of the header + gap + items
}

impl GrawFrameHeader {
    /// Sanity Checks
    pub fn check_header(&mut self, buffer_length: u32) -> Result<(), GrawFrameError> {
        if self.meta_type != EXPECTED_META_TYPE {
            return Err(GrawFrameError::IncorrectMetaType(self.meta_type));
        }
        if self.frame_size * SIZE_UNIT != buffer_length {
            return Err(GrawFrameError::IncorrectFrameSize(
                self.frame_size,
                buffer_length,
            ));
        }
        if self.frame_type != EXPECTED_FRAME_TYPE_FULL
            && self.frame_type != EXPECTED_FRAME_TYPE_PARTIAL
        {
            return Err(GrawFrameError::IncorrectFrameType(self.frame_type));
        }
        if self.header_size != EXPECTED_HEADER_SIZE {
            return Err(GrawFrameError::IncorrectHeaderSize(self.header_size));
        }
        if self.frame_type == EXPECTED_FRAME_TYPE_FULL && self.item_size != EXPECTED_ITEM_SIZE_FULL
        {
            return Err(GrawFrameError::IncorrectItemSize(self.item_size));
        } else if self.frame_type == EXPECTED_FRAME_TYPE_PARTIAL
            && self.item_size != EXPECTED_ITEM_SIZE_PARTIAL
        {
            return Err(GrawFrameError::IncorrectItemSize(self.item_size));
        }
        let calc_frame_size = (((self.n_items as f64) * (self.item_size as f64)
            + (self.header_size as f64) * (SIZE_UNIT as f64))
            / (SIZE_UNIT as f64))
            .ceil() as u32;
        if self.frame_size != calc_frame_size {
            self.n_items = (self.frame_size as u32 * SIZE_UNIT
                - self.header_size as u32 * SIZE_UNIT)
                / self.item_size as u32;
        }
        Ok(())
    }

    /// Extract the header from a buffer
    pub fn from_buffer(buf: &Vec<u8>) -> Result<GrawFrameHeader, GrawFrameError> {
        let mut cursor = Cursor::new(buf);
        let mut header = GrawFrameHeader::default();
        header.meta_type = cursor.read_u8()?;
        header.frame_size = cursor.read_u24::<BigEndian>()?; //Obnoxious. Actually a 24 bit word
        header.data_source = cursor.read_u8()?;
        header.frame_type = cursor.read_u16::<BigEndian>()?;
        header.revision = cursor.read_u8()?;
        header.header_size = cursor.read_u16::<BigEndian>()?;
        header.item_size = cursor.read_u16::<BigEndian>()?;
        header.n_items = cursor.read_u32::<BigEndian>()?;
        header.event_time = cursor.read_u48::<BigEndian>()?; //Obnoxious. Actually a 48 bit word
        header.event_id = cursor.read_u32::<BigEndian>()?;
        header.cobo_id = cursor.read_u8()?;
        header.asad_id = cursor.read_u8()?;
        header.read_offset = cursor.read_u16::<BigEndian>()?;
        header.status = cursor.read_u8()?;
        header.total_size_precise = (header.header_size as u32 * SIZE_UNIT
            + header.n_items * header.item_size as u32) as u64;
        Ok(header)
    }
}

/// A GrawFrame is the basic data chunk of the .graw format. It contains the data from a AsAd on a CoBo for a specific
/// event. GrawFrames are sized by 256 bit chunking. The header comprises one 256 bit chunks, and the body can contain several 256 bit chunks.
/// ## Note
/// Using 256 bit sizing is interesting because it often results in padding in both the body and the header. (It is done for performance reasons in the acquisition)
#[derive(Debug)]
#[allow(dead_code)]
pub struct GrawFrame {
    pub header: GrawFrameHeader,
    hit_patterns: Vec<BitVec<u8>>,
    multiplicity: Vec<u16>,
    pub data: Vec<GrawData>,
}

impl GrawFrame {
    /// Default constructor
    pub fn new(header: GrawFrameHeader) -> GrawFrame {
        GrawFrame {
            header,
            hit_patterns: vec![],
            multiplicity: vec![],
            data: vec![],
        }
    }

    pub fn read(&mut self, buffer: Vec<u8>) -> Result<(), GrawFrameError> {
        let buffer_length: u64 = buffer.len() as u64;
        let mut cursor = Cursor::new(buffer);

        self.header.check_header(buffer_length as u32)?;
        let end_position =
            cursor.position() + (self.header.n_items * self.header.item_size as u32) as u64; // Dont read the padding! Use actual size from items

        if self.header.frame_type == EXPECTED_FRAME_TYPE_PARTIAL {
            self.extract_partial_data(&mut cursor, end_position)?;
        } else if self.header.frame_type == EXPECTED_FRAME_TYPE_FULL {
            self.extract_full_data(&mut cursor, end_position)?;
        }

        Ok(())
    }

    /// Extract the data from the frame body. Idk what partial refers to here. Parsing done in 32-bit data words
    fn extract_partial_data(
        &mut self,
        cursor: &mut Cursor<Vec<u8>>,
        end_position: u64,
    ) -> Result<(), GrawFrameError> {
        let mut datum: GrawData;
        let mut raw: u32;

        while cursor.position() < end_position {
            datum = GrawData::default();

            raw = cursor.read_u32::<BigEndian>()?;
            datum.aget_id = GrawFrame::extract_aget_id(&raw);
            datum.channel = GrawFrame::extract_channel(&raw);
            datum.time_bucket_id = GrawFrame::extract_time_bucket_id(&raw);
            datum.sample = GrawFrame::extract_sample(&raw);

            match datum.check_data() {
                Ok(()) => (),
                Err(_) => {
                    continue;
                }
            }

            self.data.push(datum);
        }

        Ok(())
    }

    /// Extract the data from the frame body. Idk what full refers to here. Parsing done in 16-bit data words
    fn extract_full_data(
        &mut self,
        cursor: &mut Cursor<Vec<u8>>,
        end_position: u64,
    ) -> Result<(), GrawFrameError> {
        let mut datum: GrawData;
        let mut raw: u16;
        let mut aget_counters: Vec<u64> = vec![0, 0, 0, 0];

        while cursor.position() < end_position {
            datum = GrawData::default();
            raw = cursor.read_u16::<BigEndian>()?;
            datum.aget_id = GrawFrame::extract_aget_id_full(&raw);
            let aget_index: usize = datum.aget_id as usize;
            datum.sample = GrawFrame::extract_sample_full(&raw);
            datum.time_bucket_id = (aget_counters[aget_index] / 68) as u16; //integer division always rounds down
            datum.channel = (aget_counters[aget_index] % 68) as u8; // % operator in Rust is the remainder

            datum.check_data()?;

            self.data.push(datum);

            aget_counters[aget_index] += 1;
        }

        Ok(())
    }

    fn extract_aget_id(raw_item: &u32) -> u8 {
        ((raw_item & 0xC0000000) >> 30) as u8
    }

    fn extract_channel(raw_item: &u32) -> u8 {
        ((raw_item & 0x3F800000) >> 23) as u8
    }

    fn extract_time_bucket_id(raw_item: &u32) -> u16 {
        ((raw_item & 0x007FC000) >> 14) as u16
    }

    fn extract_sample(raw_item: &u32) -> i16 {
        (raw_item & 0x00000FFF) as i16
    }

    fn extract_aget_id_full(raw_item: &u16) -> u8 {
        ((raw_item & 0xC000) >> 14) as u8
    }

    fn extract_sample_full(raw_item: &u16) -> i16 {
        (raw_item & 0x0FFF) as i16
    }
}
