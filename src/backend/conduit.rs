use numpy::IntoPyArray;
use numpy::PyArray2;
use std::path::PathBuf;
use tokio::sync::broadcast;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;

use pyo3::prelude::*;

use super::constants::DEFAULT_SERVER_PORT;
use super::constants::NUMBER_OF_COBOS;
use super::ecc_reciever::startup_ecc_recievers;
use super::event::Event;
use super::event_builder::startup_event_builder;
use super::graw_frame::GrawFrame;
use super::message::ConduitMessage;
use super::pad_map::PadMap;
use super::point_cloud::PointCloud;
use super::server::startup_server;

#[pyclass]
#[derive(Debug)]
pub struct Conduit {
    event_receiver: Option<mpsc::Receiver<Event>>,
    cancel_sender: broadcast::Sender<ConduitMessage>,
    cloud_sender: broadcast::Sender<PointCloud>,
    runtime: tokio::runtime::Runtime,
    handles: Option<Vec<JoinHandle<()>>>,
    server_port: String,
}

#[pymethods]
impl Conduit {
    #[new]
    pub fn new() -> Self {
        let rt = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(11)
            .enable_time()
            .enable_io()
            .build()
            .expect("Could not build tokio runtime!");

        let (cancel_tx, _) = broadcast::channel(11);
        let (cloud_tx, _) = broadcast::channel(10);

        Self {
            event_receiver: None,
            cancel_sender: cancel_tx,
            cloud_sender: cloud_tx,
            runtime: rt,
            handles: None,
            server_port: String::from(DEFAULT_SERVER_PORT),
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

        let server_handle = startup_server(
            &self.runtime,
            self.cloud_sender.clone(),
            self.cancel_sender.clone(),
            self.server_port.clone(),
        );
        handles.push(server_handle);

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

    pub fn poll_events<'py>(&mut self, py: Python<'py>) -> Option<&'py PyArray2<i16>> {
        match self.event_receiver.as_mut() {
            Some(rx) => match rx.try_recv() {
                Ok(event) => Some(event.convert_to_data_matrix().into_pyarray(py)),
                Err(_) => None,
            },
            None => None,
        }
    }

    pub fn submit_point_cloud(&mut self, cloud_buffer: Vec<u8>) {
        let cloud = PointCloud::new(cloud_buffer);
        match self.cloud_sender.send(cloud) {
            Ok(_) => (),
            Err(e) => tracing::error!("Could not send a point cloud!"),
        }
    }
}
