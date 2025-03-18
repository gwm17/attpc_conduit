use numpy::IntoPyArray;
use numpy::PyArray2;
use std::path::PathBuf;
use tokio::sync::broadcast;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;

use pyo3::prelude::*;

use super::backend::constants::NUMBER_OF_COBOS;
use super::backend::error::ConduitError;
use super::backend::event::Event;
use super::backend::event_builder::startup_event_builder;
use super::backend::exporter_receiver::startup_exporter_recievers;
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
    handles: Option<Vec<JoinHandle<Result<(), ConduitError>>>>,
    pad_path: PathBuf,
}

#[pymethods]
impl Conduit {
    /// Create a new Conduit. Requires a path to a pad map.
    #[new]
    pub fn new(pad_path: PathBuf, n_threads: usize) -> Self {
        let rt = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(n_threads)
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
            pad_path,
        }
    }

    /// Initialize and start all of the backend services
    pub fn connect(&mut self, max_cache_size: usize) {
        if self.handles.is_some() {
            log::warn!("Could not start services, as they're already started!");
            return;
        }

        log::info!("Creating communication channels and loading pad map...");
        let (frame_tx, frame_rx) = mpsc::channel::<GrawFrame>(40);
        let (event_tx, event_rx) = mpsc::channel::<Event>(40);
        let pad_map = match PadMap::new(&self.pad_path) {
            Ok(map) => map,
            Err(e) => {
                log::error!("PadMap ran into a problem: {e}");
                return;
            }
        };

        log::info!("Starting DataExporter communication...");
        let mut handles = startup_exporter_recievers(&self.runtime, &frame_tx, &self.cancel_sender);
        if handles.len() < NUMBER_OF_COBOS as usize {
            log::warn!(
                "There was an issue spawning DataExporter receivers! Only spawned {} receivers",
                handles.len()
            )
        }

        log::info!("Starting Event Builder communication...");
        let evb_handle = startup_event_builder(
            &self.runtime,
            frame_rx,
            event_tx,
            &self.cancel_sender,
            pad_map,
            max_cache_size,
        );
        handles.push(evb_handle);

        self.handles = Some(handles);
        self.event_receiver = Some(event_rx);

        log::info!("Communication started.");
    }

    /// Shutdown all of the backend services
    pub fn disconnect(&mut self) {
        if self.handles.is_none() {
            log::warn!("Could not stop services as there weren't any active!");
            return;
        }

        log::info!("Stopping all Conduit services...");

        let handles = self.handles.take().expect("This literally cannot happen");
        self.cancel_sender
            .send(ConduitMessage::Cancel)
            .expect("Somehow all the services were already dead");
        for handle in handles {
            match self.runtime.block_on(handle) {
                Ok(res) => match res {
                    Ok(_) => (),
                    Err(e) => log::error!("One of the services had an error: {}", e),
                },
                Err(e) => log::error!("Error whilst joining services: {}", e),
            }
        }
        log::info!("Conduit stopped.");
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

    /// See if the conduit is connected to it's receivers
    pub fn is_connected(&self) -> bool {
        self.handles.is_some()
    }
}
