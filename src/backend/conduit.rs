use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::broadcast;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;

use super::constants::NUMBER_OF_COBOS;
use super::ecc_reciever::startup_ecc_recievers;
use super::event::Event;
use super::event_builder::startup_event_builder;
use super::graw_frame::GrawFrame;
use super::message::ConduitMessage;
use super::pad_map::PadMap;

#[derive(Debug)]
struct Conduit {
    event_receiver: Option<mpsc::Receiver<Event>>,
    cancel_sender: broadcast::Sender<ConduitMessage>,
    runtime: tokio::runtime::Runtime,
    handles: Option<Vec<JoinHandle<()>>>,
}

impl Conduit {
    pub fn new(rt: &Arc<tokio::runtime::Runtime>) -> Self {
        let rt = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(11)
            .enable_time()
            .enable_io()
            .build()
            .expect("Could not build tokio runtime!");

        let (cancel_tx, _) = broadcast::channel(11);

        Self {
            event_receiver: None,
            cancel_sender: cancel_tx,
            runtime: rt,
            handles: None,
        }
    }

    pub fn start_services(&mut self) {
        if !self.handles.is_none() {
            tracing::warn!("Could not start services, as they're already started!");
            return;
        }

        let (frame_tx, frame_rx) = mpsc::channel::<GrawFrame>(40);
        let (event_tx, event_rx) = mpsc::channel::<Event>(40);
        let pad_map = PadMap::new(&PathBuf::from("/some/path")).unwrap(); //Fix this later!

        let mut handles = startup_ecc_recievers(&self.runtime, &frame_tx, &self.cancel_sender);
        if handles.len() < NUMBER_OF_COBOS as usize {
            tracing::warn!(
                "There was an issue spawning ECCReceivers! Only spawned {} receivers",
                handles.len()
            )
        }

        let evb_handle = startup_event_builder(
            &self.runtime,
            frame_rx,
            event_tx,
            &self.cancel_sender,
            pad_map,
        );
        handles.push(evb_handle);
        self.handles = Some(handles);
        self.event_receiver = Some(event_rx);
    }

    pub fn stop_services(&mut self) {
        if self.handles.is_none() {
            tracing::warn!("Could not stop services as there weren't any active!");
            return;
        }

        let handles = self.handles.take().expect("This literally cannot happen");
        self.cancel_sender
            .send(ConduitMessage::Cancel)
            .expect("Somehow all the services were already dead");
        for handle in handles {
            match self.runtime.block_on(handle) {
                Ok(()) => (),
                Err(e) => tracing::error!("Error whilst joining services: {}", e),
            }
        }
    }

    pub fn poll_events(&mut self) -> Option<Event> {
        match self.event_receiver.as_mut() {
            Some(rx) => match rx.try_recv() {
                Ok(event) => Some(event),
                Err(_) => None,
            },
            None => None,
        }
    }
}
