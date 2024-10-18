use numpy::IntoPyArray;
use numpy::PyArray2;
use std::path::PathBuf;
use tokio::sync::broadcast;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;
use tracing_subscriber;

use pyo3::prelude::*;

use super::backend::constants::NUMBER_OF_COBOS;
use super::backend::ecc_reciever::startup_ecc_recievers;
use super::backend::event::Event;
use super::backend::event_builder::startup_event_builder;
use super::backend::graw_frame::GrawFrame;
use super::backend::message::ConduitMessage;
use super::backend::pad_map::PadMap;

/// The Conduit is the main interface for controlling the behavior of the backend
/// as well as exposing events to further analysis pipelines. Conduit is python compatible
/// with all of it's methods exposed to Python.
#[pyclass]
#[derive(Debug)]
pub struct Conduit {
    event_receiver: Option<mpsc::Receiver<Event>>,
    cancel_sender: broadcast::Sender<ConduitMessage>,
    runtime: tokio::runtime::Runtime,
    handles: Option<Vec<JoinHandle<()>>>,
    pad_path: PathBuf,
}

#[pymethods]
impl Conduit {
    /// Create a new Conduit. Requires a path to a pad map.
    #[new]
    pub fn new(pad_path: PathBuf) -> Self {
        let rt = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(11)
            .enable_time()
            .enable_io()
            .build()
            .expect("Could not build tokio runtime!");

        let (cancel_tx, _) = broadcast::channel(11);

        //Create our logging/tracing system.
        let subscriber = tracing_subscriber::fmt()
            .compact()
            .with_file(true)
            .with_line_number(true)
            .with_thread_ids(true)
            .with_target(false)
            .finish();
        tracing::subscriber::set_global_default(subscriber)
            .expect("Could not initialize the tracing system!");

        Self {
            event_receiver: None,
            cancel_sender: cancel_tx,
            runtime: rt,
            handles: None,
            pad_path,
        }
    }

    /// Initialize and start all of the backend services
    pub fn start_services(&mut self) {
        if !self.handles.is_none() {
            tracing::warn!("Could not start services, as they're already started!");
            return;
        }

        tracing::info!("Creating communication channels and loading pad map...");
        let (frame_tx, frame_rx) = mpsc::channel::<GrawFrame>(40);
        let (event_tx, event_rx) = mpsc::channel::<Event>(40);
        let pad_map = match PadMap::new(&self.pad_path) {
            Ok(map) => map,
            Err(e) => {
                tracing::error!("{e}");
                return;
            }
        };

        tracing::info!("Starting ECC communication...");
        let mut handles = startup_ecc_recievers(&self.runtime, &frame_tx, &self.cancel_sender);
        if handles.len() < NUMBER_OF_COBOS as usize {
            tracing::warn!(
                "There was an issue spawning ECCReceivers! Only spawned {} receivers",
                handles.len()
            )
        }

        tracing::info!("Starting Event Builder communication...");
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

        tracing::info!("Communication started.");
    }

    /// Shutdown all of the backend services
    pub fn stop_services(&mut self) {
        if self.handles.is_none() {
            tracing::warn!("Could not stop services as there weren't any active!");
            return;
        }

        tracing::info!("Stopping all Conduit services...");

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
        tracing::info!("Stopped.");
    }

    /// Poll the conduit for any new events. The events are marshalled to Python numpy arrarys.
    pub fn poll_events<'py>(
        &mut self,
        py: Python<'py>,
    ) -> Option<(u32, Bound<'py, PyArray2<i16>>)> {
        match self.event_receiver.as_mut() {
            Some(rx) => match rx.try_recv() {
                Ok(event) => Some((
                    event.get_event_id(),
                    event.convert_to_data_matrix().into_pyarray_bound(py),
                )),
                Err(_) => None,
            },
            None => None,
        }
    }
}
