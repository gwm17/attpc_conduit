use std::collections::VecDeque;

use fxhash::FxHashMap;
use tokio::sync::{broadcast, mpsc};
use tokio::task::JoinHandle;

use crate::backend::constants::MAX_FRAME_CACHE;

use super::error::{ConduitError, EventBuilderError};
use super::event::Event;
use super::graw_frame::GrawFrame;
use super::message::ConduitMessage;
use super::pad_map::PadMap;

/// An EventCache is a storage system for event data. In live data taking, modules
/// may fill their internal memory buffers at different rates, resulting in chunks of
/// the same physical event being transmitted at different times. To handle this, we
/// cache events, building multiple events at the same time. Once we reach a size
/// limit, the least recently modified event is popped from the cache.
#[derive(Debug)]
struct EventCache {
    events: FxHashMap<u32, Event>,
    order: VecDeque<u32>,
}

impl EventCache {
    /// Create a new cache
    pub fn new() -> Self {
        EventCache {
            events: FxHashMap::default(),
            order: VecDeque::new(),
        }
    }

    /// Add a frame to the cache. If there is no event to which this frame
    /// corresponds, a new event is created for it.
    pub fn add_frame(
        &mut self,
        pad_map: &PadMap,
        frame: GrawFrame,
    ) -> Result<(), EventBuilderError> {
        let frame_evt_id = frame.header.event_id;
        match self.events.get_mut(&frame_evt_id) {
            Some(event) => {
                event.append_frame(pad_map, frame)?;
                let mut event_position = 0;
                for (idx, event_id) in self.order.iter().enumerate() {
                    if *event_id == frame_evt_id {
                        event_position = idx;
                        break;
                    }
                }
                self.order.remove(event_position);
                self.order.push_back(frame_evt_id);
            }
            None => {
                let mut event = Event::new();
                event.append_frame(pad_map, frame)?;
                self.events.insert(frame_evt_id, event);
                self.order.push_back(frame_evt_id);
            }
        }

        Ok(())
    }

    /// Returns the least recently used event
    pub fn get_lru_event(&mut self) -> Result<Event, EventBuilderError> {
        if let Some(least_recently_used) = self.order.pop_front() {
            Ok(self.events.remove(&least_recently_used).expect(&format!(
                "Some how frame cache didn't have event {least_recently_used}!"
            )))
        } else {
            Err(EventBuilderError::BrokenCache)
        }
    }

    /// Returns the size of the cache in GRAW Frames
    pub fn size(&self) -> usize {
        self.events
            .iter()
            .fold(0, |acc, (_, event)| acc + event.get_nframes())
    }
}

/// EventBuilder receives GrawFrames from the various receivers and composes them into
/// events. It then transmits events to the Conduit, where they can be polled by other
/// pipelines.
#[derive(Debug)]
#[allow(dead_code)]
pub struct EventBuilder {
    current_event_id: u32,
    pad_map: PadMap,
    frame_receiver: mpsc::Receiver<GrawFrame>,
    event_sender: mpsc::Sender<Event>,
    event_cache: EventCache,
}

impl EventBuilder {
    /// Create a new EventBuilder. Requires a PadMap
    pub fn new(
        pad_map: PadMap,
        frame_rx: mpsc::Receiver<GrawFrame>,
        event_tx: mpsc::Sender<Event>,
    ) -> Self {
        EventBuilder {
            current_event_id: 0,
            pad_map,
            frame_receiver: frame_rx,
            event_sender: event_tx,
            event_cache: EventCache::new(),
        }
    }

    /// The main task of the EventBuilder to be spawned
    pub async fn run(
        &mut self,
        cancel: &mut broadcast::Receiver<ConduitMessage>,
    ) -> Result<(), EventBuilderError> {
        loop {
            tokio::select! {
                _ = cancel.recv() => {
                    return Ok(());
                }
                _ = self.read_and_send() => ()
            }
        }
    }

    /// Reads the GrawFrame from an ECCReceiver and adds it to the event cache.
    /// If the cache is full, an event is sent up to the conduit for exposure.
    async fn read_and_send(&mut self) -> Result<(), EventBuilderError> {
        let new_frame = match self.frame_receiver.recv().await {
            Some(frame) => frame,
            None => return Err(EventBuilderError::ClosedChannel),
        };

        self.event_cache.add_frame(&self.pad_map, new_frame)?;

        if self.event_cache.size() > MAX_FRAME_CACHE {
            self.event_sender
                .send(self.event_cache.get_lru_event()?)
                .await?
        }

        Ok(())
    }
}

/// Helper function for starting the EventBuilder
pub fn startup_event_builder(
    rt: &tokio::runtime::Runtime,
    frame_rx: mpsc::Receiver<GrawFrame>,
    event_tx: mpsc::Sender<Event>,
    cancel: &broadcast::Sender<ConduitMessage>,
    pad_map: PadMap,
) -> JoinHandle<Result<(), ConduitError>> {
    let mut evb = EventBuilder::new(pad_map, frame_rx, event_tx);
    let mut cancel_rx = cancel.subscribe();
    rt.spawn(async move {
        match evb.run(&mut cancel_rx).await {
            Ok(()) => Ok(()),
            Err(e) => Err(ConduitError::FailedEventBuilder(e)),
        }
    })
}
