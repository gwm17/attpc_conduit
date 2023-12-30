use std::error::Error;
use std::fmt::Display;

use super::constants::*;

/*
   GrawData errors
*/
#[derive(Debug, Clone)]
pub enum GrawDataError {
    BadAgetID(u8),
    BadChannel(u8),
    BadTimeBucket(u16),
}

impl Display for GrawDataError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GrawDataError::BadAgetID(id) => write!(f, "Invalid aget ID {} found in GrawData!", id),
            GrawDataError::BadChannel(chan) => {
                write!(f, "Invalid channel {} found in GrawData!", chan)
            }
            GrawDataError::BadTimeBucket(bucket) => {
                write!(f, "Invalid time bucket {} found in GrawData!", bucket)
            }
        }
    }
}

impl Error for GrawDataError {}

/*
   GrawFrame errors
*/
#[derive(Debug)]
pub enum GrawFrameError {
    IOError(std::io::Error),
    IncorrectMetaType(u8),
    IncorrectFrameSize(u32, u32),
    IncorrectFrameType(u16),
    IncorrectHeaderSize(u16),
    IncorrectItemSize(u16),
    BadDatum(GrawDataError),
}

impl From<std::io::Error> for GrawFrameError {
    fn from(value: std::io::Error) -> Self {
        Self::IOError(value)
    }
}

impl From<GrawDataError> for GrawFrameError {
    fn from(value: GrawDataError) -> Self {
        GrawFrameError::BadDatum(value)
    }
}

impl Display for GrawFrameError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GrawFrameError::IOError(e) => write!(f, "Error parsing buffer into GrawFrame: {}", e),
            GrawFrameError::IncorrectMetaType(t) => write!(
                f,
                "Incorrect meta type found for GrawFrame! Found: {} Expected: {}",
                t, EXPECTED_META_TYPE
            ),
            GrawFrameError::IncorrectFrameSize(s, cs) => write!(
                f,
                "Incorrect frame size found for GrawFrame! Found: {}, Expected: {}",
                s, cs
            ),
            GrawFrameError::IncorrectFrameType(t) => write!(
                f,
                "Incorrect frame type found for GrawFrame! Found: {}, Expected: {} or {}",
                t, EXPECTED_FRAME_TYPE_FULL, EXPECTED_FRAME_TYPE_PARTIAL
            ),
            GrawFrameError::IncorrectHeaderSize(s) => write!(
                f,
                "Incorrect header size found for GrawFrame! Found: {}, Expected: {}",
                s, EXPECTED_HEADER_SIZE
            ),
            GrawFrameError::IncorrectItemSize(s) => write!(
                f,
                "Incorrect item size found for GrawFrame! Found: {}, Expected: {} or {}",
                s, EXPECTED_ITEM_SIZE_FULL, EXPECTED_ITEM_SIZE_PARTIAL
            ),
            GrawFrameError::BadDatum(e) => write!(f, "Bad datum found in GrawFrame! Error: {}", e),
        }
    }
}

impl Error for GrawFrameError {}

/*
   ECCReceiver errors
*/

#[derive(Debug)]
pub enum ECCReceiverError {
    BadFrame(GrawFrameError),
    AddressParseError,
    EndOfStream,
    IOError(std::io::Error),
    Timeout(tokio::time::error::Elapsed),
}

impl From<GrawFrameError> for ECCReceiverError {
    fn from(value: GrawFrameError) -> Self {
        Self::BadFrame(value)
    }
}

impl From<std::io::Error> for ECCReceiverError {
    fn from(value: std::io::Error) -> Self {
        Self::IOError(value)
    }
}

impl From<std::net::AddrParseError> for ECCReceiverError {
    fn from(value: std::net::AddrParseError) -> Self {
        Self::AddressParseError
    }
}

impl From<tokio::time::error::Elapsed> for ECCReceiverError {
    fn from(value: tokio::time::error::Elapsed) -> Self {
        Self::Timeout(value)
    }
}

impl Display for ECCReceiverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::BadFrame(frame) => {
                write!(f, "Bad frame found when reading GrawFile! Error: {}", frame)
            }
            Self::AddressParseError => write!(f, "Bad IP address and socket at ECCReciever"),
            Self::EndOfStream => write!(f, "ECCReciever ended"),
            Self::IOError(e) => write!(f, "GrawFile recieved an io error: {}!", e),
            Self::Timeout(e) => write!(f, "Attepmt to connect ECCReceiver timed out! {}", e),
        }
    }
}

impl Error for ECCReceiverError {}

/*
   PadMap errors
*/

#[derive(Debug)]
pub enum PadMapError {
    IOError(std::io::Error),
    ParsingError(std::num::ParseIntError),
    BadFileFormat,
}

impl From<std::io::Error> for PadMapError {
    fn from(value: std::io::Error) -> Self {
        PadMapError::IOError(value)
    }
}

impl From<std::num::ParseIntError> for PadMapError {
    fn from(value: std::num::ParseIntError) -> Self {
        PadMapError::ParsingError(value)
    }
}

impl Display for PadMapError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PadMapError::IOError(e) => write!(f, "PadMap recieved an io error: {}", e),
            PadMapError::ParsingError(e) => write!(f, "PadMap error recieved a parsing error: {}", e),
            PadMapError::BadFileFormat => write!(f, "PadMap found a bad file format while reading the map file! Expected .csv without whitespaces")
        }
    }
}

impl Error for PadMapError {}

/*
   Event errors
*/
#[derive(Debug)]
#[allow(dead_code)]
pub enum EventError {
    InvalidHardware(u8, u8, u8, u8),
    MismatchedEventID(u32, u32),
}

impl Display for EventError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EventError::InvalidHardware(cb, ad, ag, ch) => write!(f, "Event found hardware which does not correspond to a valid pad! CoBo: {}, AsAd: {}, AGET: {}, Channel: {}", cb, ad, ag, ch),
            EventError::MismatchedEventID(given, exp) => write!(f, "Event was given a mismatched event id! Given: {}, Expected: {}", given, exp)
        }
    }
}

impl Error for EventError {}

/*
   EventBuilder errors
*/

#[derive(Debug)]
pub enum EventBuilderError {
    EventOutOfOrder(u32, u32),
    EventError(EventError),
    BrokenCache,
    ClosedChannel,
}

impl From<EventError> for EventBuilderError {
    fn from(value: EventError) -> Self {
        Self::EventError(value)
    }
}

impl Display for EventBuilderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EventOutOfOrder(frame, event) => write!(f, "The event builder recieved a frame that is out of order -- frame event id: {} event builder event id: {}", frame, event),
            Self::EventError(val) => write!(f, "The EventBuilder recieved an event error: {}", val),
            Self::BrokenCache => write!(f, "The EventBuilder event cache was broken (mismatched order/cache)!"),
            Self::ClosedChannel => write!(f, "The EventBuilder had a closed channel!")
        }
    }
}

impl Error for EventBuilderError {}

#[derive(Debug)]
pub enum ServerError {
    IOError(std::io::Error),
    Timeout(tokio::time::error::Elapsed),
}

impl From<std::io::Error> for ServerError {
    fn from(value: std::io::Error) -> Self {
        Self::IOError(value)
    }
}

impl From<tokio::time::error::Elapsed> for ServerError {
    fn from(value: tokio::time::error::Elapsed) -> Self {
        Self::Timeout(value)
    }
}

impl Display for ServerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::IOError(e) => write!(f, "The server ran into an IO error: {e}"),
            Self::Timeout(e) => write!(f, "The server timed out on a connection: {e}"),
        }
    }
}

impl Error for ServerError {}
