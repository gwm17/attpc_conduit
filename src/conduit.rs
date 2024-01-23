use numpy::IntoPyArray;
use numpy::PyArray2;
use std::path::PathBuf;
use tokio::sync::broadcast;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;
use tracing_subscriber;

use pyo3::prelude::*;

use super::backend::constants::DEFAULT_SERVER_PORT;
use super::backend::constants::NUMBER_OF_COBOS;
use super::backend::ecc_reciever::startup_ecc_recievers;
use super::backend::event::Event;
use super::backend::event_builder::startup_event_builder;
use super::backend::graw_frame::GrawFrame;
use super::backend::message::ConduitMessage;
use super::backend::pad_map::PadMap;
use super::backend::point_cloud::PointCloud;
use super::backend::server::startup_server;

#[pyclass]
#[derive(Debug)]
pub struct Conduit {
    event_receiver: Option<mpsc::Receiver<Event>>,
    cancel_sender: broadcast::Sender<ConduitMessage>,
    cloud_sender: broadcast::Sender<PointCloud>,
    runtime: tokio::runtime::Runtime,
    handles: Option<Vec<JoinHandle<()>>>,
    server_port: String,
    pad_path: PathBuf,
}

#[pymethods]
impl Conduit {
    #[new]
    pub fn new(pad_path: PathBuf) -> Self {
        let rt = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(11)
            .enable_time()
            .enable_io()
            .build()
            .expect("Could not build tokio runtime!");

        let (cancel_tx, _) = broadcast::channel(11);
        let (cloud_tx, _) = broadcast::channel(10);

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

        tracing::info!("Can you hear me?");
        Self {
            event_receiver: None,
            cancel_sender: cancel_tx,
            cloud_sender: cloud_tx,
            runtime: rt,
            handles: None,
            server_port: String::from(DEFAULT_SERVER_PORT),
            pad_path,
        }
    }

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

        tracing::info!("Starting server communication...");
        let server_handle = startup_server(
            &self.runtime,
            self.cloud_sender.clone(),
            self.cancel_sender.clone(),
            self.server_port.clone(),
        );
        handles.push(server_handle);

        self.handles = Some(handles);
        self.event_receiver = Some(event_rx);

        tracing::info!("Communication started.");
    }

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

    pub fn poll_events<'py>(&mut self, py: Python<'py>) -> Option<(u32, &'py PyArray2<i16>)> {
        match self.event_receiver.as_mut() {
            Some(rx) => match rx.try_recv() {
                Ok(event) => Some((
                    event.get_event_id(),
                    event.convert_to_data_matrix().into_pyarray(py),
                )),
                Err(_) => None,
            },
            None => None,
        }
    }

    pub fn submit_point_cloud(&mut self, cloud_buffer: Vec<u8>) {
        let cloud = PointCloud::new(cloud_buffer);
        match self.cloud_sender.send(cloud) {
            Ok(_) => (),
            Err(_) => tracing::error!("Could not send a point cloud!"),
        }
    }
}
