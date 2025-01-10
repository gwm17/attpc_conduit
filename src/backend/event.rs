use fxhash::FxHashMap;
use numpy::ndarray::{s, Array1, Array2};

use super::constants::*;
use super::error::EventError;
use super::graw_frame::GrawFrame;
use super::pad_map::{HardwareID, PadMap};

/// An event is a collection of traces which all occured with the same Event ID
/// generated by the AT-TPC GET DAQ. An event is created from a Vec of GrawFrames,
/// which are then parsed into ndarray traces. The event can also subtract
/// the fixed pattern noise recored by the electronics. To write the event to HDF5 or
/// marshall the data to Python we must convert the event to a data matrix.
#[derive(Debug)]
pub struct Event {
    nframes: i32,
    traces: FxHashMap<HardwareID, Array1<i16>>, //maps pad id to the trace for that pad
    timestamp: u64,
    timestampother: u64,
    event_id: u32,
}

impl Event {
    /// Make a new empty event
    pub fn new() -> Self {
        Event {
            nframes: 0,
            traces: FxHashMap::default(),
            timestamp: 0,
            timestampother: 0,
            event_id: 0,
        }
    }

    /// Convert the event traces to a data matrix for writing to disk or marshalling to
    /// Python. Follows format used by AT-TPC analysis
    pub fn convert_to_data_matrix(self) -> Array2<i16> {
        let mut data_matrix = Array2::<i16>::zeros([self.traces.len(), NUMBER_OF_MATRIX_COLUMNS]);
        for (row, (hw_id, trace)) in self.traces.into_iter().enumerate() {
            data_matrix[[row, 0]] = hw_id.cobo_id as i16;
            data_matrix[[row, 1]] = hw_id.asad_id as i16;
            data_matrix[[row, 2]] = hw_id.aget_id as i16;
            data_matrix[[row, 3]] = hw_id.channel as i16;
            data_matrix[[row, 4]] = hw_id.pad_id as i16;
            let mut trace_slice = data_matrix.slice_mut(s![row, 5..NUMBER_OF_MATRIX_COLUMNS]);
            trace.move_into(&mut trace_slice);
        }

        data_matrix
    }

    /// Add a frame to the event. Sanity checks can return errors
    pub fn append_frame(&mut self, pad_map: &PadMap, frame: GrawFrame) -> Result<(), EventError> {
        if self.nframes == 0 {
            //first frame
            self.event_id = frame.header.event_id;
        } else if self.event_id != frame.header.event_id {
            return Err(EventError::MismatchedEventID(
                frame.header.event_id,
                self.event_id,
            ));
        }

        if frame.header.cobo_id == COBO_WITH_TIMESTAMP && self.timestampother == 0 {
            // this cobo has a TS in sync with other DAQ
            self.timestampother = frame.header.event_time;
        } else if self.timestamp == 0 {
            // all other cobos have the same TS from Mutant
            self.timestamp = frame.header.event_time;
        }

        for datum in frame.data.iter() {
            if let Some(hw_id) = pad_map.get_hardware_id(
                &frame.header.cobo_id,
                &frame.header.asad_id,
                &datum.aget_id,
                &datum.channel,
            ) {
                match self.traces.get_mut(hw_id) {
                    Some(trace) => {
                        trace[datum.time_bucket_id as usize] = datum.sample;
                    }
                    None => {
                        //First time this pad found during event. Create a new array
                        let mut trace: Array1<i16> =
                            Array1::<i16>::zeros(NUMBER_OF_TIME_BUCKETS as usize);
                        trace[datum.time_bucket_id as usize] = datum.sample;
                        self.traces.insert(hw_id.clone(), trace);
                    }
                }
            }
        }

        self.nframes += 1;

        Ok(())
    }

    /// Get the total number of frames in the event
    pub fn get_nframes(&self) -> usize {
        self.nframes as usize
    }

    pub fn get_event_id(&self) -> u32 {
        self.event_id
    }
}
