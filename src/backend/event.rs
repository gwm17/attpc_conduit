use fxhash::FxHashMap;
use numpy::ndarray::{s, Array1, Array2};

use super::constants::*;
use super::error::EventError;
use super::graw_frame::GrawFrame;
use super::pad_map::{HardwareID, PadMap};

const FPN_CHANNELS: [u8; 4] = [11, 22, 45, 56]; //From AGET docs

/// An event is a collection of traces which all occured with the same Event ID generated by the AT-TPC GET DAQ.
/// An event is created from a Vec of GrawFrames, which are then parsed into ndarray traces. The event can also subtract
/// the fixed pattern noise recored by the electronics. To write the event to HDF5 or marshall the data to Python we must
/// convert the event to a data matrix.
#[derive(Debug)]
pub struct Event {
    nframes: i32,
    traces: FxHashMap<HardwareID, Array1<i16>>, //maps pad id to the trace for that pad
    timestamp: u64,
    timestampother: u64,
    event_id: u32,
}

impl Event {
    /// Make a new event from a list of GrawFrames
    pub fn new() -> Self {
        Event {
            nframes: 0,
            traces: FxHashMap::default(),
            timestamp: 0,
            timestampother: 0,
            event_id: 0,
        }
    }

    /// Convert the event traces to a data matrix for writing to disk or marshalling to Python. Follows format used by AT-TPC analysis
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

        return data_matrix;
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

        if frame.header.cobo_id == COBO_WITH_TIMESTAMP {
            // this cobo has a TS in sync with other DAQ
            self.timestampother = frame.header.event_time;
        } else {
            // all other cobos have the same TS from Mutant
            self.timestamp = frame.header.event_time;
        }

        let mut hw_id: &HardwareID;
        for datum in frame.data.iter() {
            hw_id = match pad_map.get_hardware_id(
                &frame.header.cobo_id,
                &frame.header.asad_id,
                &datum.aget_id,
                &datum.channel,
            ) {
                Some(hw) => hw,
                None => continue,
            };

            match self.traces.get_mut(&hw_id) {
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

        self.nframes += 1;

        Ok(())
    }

    pub fn get_nframes(&self) -> usize {
        self.nframes as usize
    }

    pub fn get_event_id(&self) -> u32 {
        self.event_id
    }

    /// Only for use in special cases! This will not throw errors when invalid pads are selected
    #[allow(dead_code)]
    fn get_trace_from_hardware_id(
        &self,
        pad_map: &PadMap,
        cobo_id: &u8,
        asad_id: &u8,
        aget_id: &u8,
        channel_id: &u8,
    ) -> Option<&Array1<i16>> {
        if let Some(hw_id) = pad_map.get_hardware_id(cobo_id, asad_id, aget_id, channel_id) {
            return self.traces.get(hw_id);
        } else {
            return None;
        }
    }

    /// Only for use in special cases! This will not throw errors when invalid pads are selected
    #[allow(dead_code)]
    fn get_mutable_trace_from_hardware_id(
        &mut self,
        pad_map: &PadMap,
        cobo_id: &u8,
        asad_id: &u8,
        aget_id: &u8,
        channel_id: &u8,
    ) -> Option<&mut Array1<i16>> {
        if let Some(hw_id) = pad_map.get_hardware_id(cobo_id, asad_id, aget_id, channel_id) {
            return self.traces.get_mut(hw_id);
        } else {
            return None;
        }
    }

    /// Remove a trace, if it exists
    #[allow(dead_code)]
    fn remove_trace(
        &mut self,
        pad_map: &PadMap,
        cobo_id: &u8,
        asad_id: &u8,
        aget_id: &u8,
        channel_id: &u8,
    ) {
        if let Some(hw_id) = pad_map.get_hardware_id(cobo_id, asad_id, aget_id, channel_id) {
            self.traces.remove(hw_id);
        }
    }

    #[allow(dead_code)]
    fn remove_fpn_channels(&mut self, pad_map: &PadMap, cobo_id: &u8, asad_id: &u8, aget_id: &u8) {
        for channel in FPN_CHANNELS {
            self.remove_trace(pad_map, &cobo_id, &asad_id, &aget_id, &channel);
        }
    }
}
