use std::net::SocketAddr;
use std::time::Duration;
use tokio::io::AsyncWriteExt;
use tokio::net::{TcpListener, TcpStream};
use tokio::runtime::Handle;
use tokio::sync::broadcast;
use tokio::task::JoinHandle;
use tokio::time::timeout;

use super::error::ServerError;
use super::message::ConduitMessage;
use super::point_cloud::PointCloud;

const CONNECTION_TIMEOUT: Duration = Duration::from_secs(120);
const SEND_TIMEOUT: Duration = Duration::from_secs(60);
const MAX_CLIENTS: usize = 3;

#[derive(Debug)]
pub struct Connection {
    socket: TcpStream,
    address: SocketAddr,
    cloud_receiver: broadcast::Receiver<PointCloud>,
}

impl Connection {
    pub fn new(
        socket: TcpStream,
        address: SocketAddr,
        receiver: broadcast::Receiver<PointCloud>,
    ) -> Self {
        Connection {
            socket,
            address,
            cloud_receiver: receiver,
        }
    }

    pub async fn run(
        &mut self,
        cancel: &mut broadcast::Receiver<ConduitMessage>,
    ) -> Result<(), ServerError> {
        loop {
            tokio::select! {
                _ = cancel.recv() => {
                    return Ok(())
                },
                cloud = self.cloud_receiver.recv() => {
                    match cloud {
                        Ok(c) => self.write(c).await?,
                        Err(_) => return Ok(()),
                    }
                }
            }
        }
    }

    async fn write(&mut self, point_cloud: PointCloud) -> Result<(), std::io::Error> {
        let buffer: Vec<u8> = point_cloud.into();
        self.socket.write_all(&buffer).await
    }
}

#[derive(Debug)]
pub struct Server {
    listener_port: String,
    listener_socket: TcpListener,
    connections: usize,
    cloud_sender: broadcast::Sender<PointCloud>,
    runtime: Handle,
}

impl Server {
    pub async fn new(
        listener_port: String,
        cloud_sender: broadcast::Sender<PointCloud>,
        runtime: Handle,
    ) -> Result<Self, ServerError> {
        let l_addr = format!(":{listener_port}");
        let l_socket = (timeout(CONNECTION_TIMEOUT, TcpListener::bind(l_addr)).await?)?;

        Ok(Self {
            listener_port,
            listener_socket: l_socket,
            connections: 0,
            cloud_sender,
            runtime,
        })
    }

    pub async fn run(
        &mut self,
        cancel: &mut broadcast::Receiver<ConduitMessage>,
        cancel_sender: &mut broadcast::Sender<ConduitMessage>,
    ) -> Result<(), ServerError> {
        loop {
            tokio::select! {
                _ = cancel.recv() => {
                    return Ok(());
                },
                _ = self.wait_and_handle_connection(cancel_sender) => (),
            }
        }
    }

    async fn wait_and_handle_connection(
        &mut self,
        cancel_sender: &mut broadcast::Sender<ConduitMessage>,
    ) -> Result<(), ServerError> {
        let (stream, addr) = self.listener_socket.accept().await?;
        if self.connections == MAX_CLIENTS {
            tracing::warn!(
                "Server is at max number of clients {}. Cannot accept another connection.",
                MAX_CLIENTS
            );
            return Ok(());
        } else {
            let this_receiver = self.cloud_sender.subscribe();
            let mut this_cancel = cancel_sender.subscribe();
            self.runtime.spawn(async move {
                let mut conn = Connection::new(stream, addr, this_receiver);
                match conn.run(&mut this_cancel).await {
                    Ok(()) => (),
                    Err(e) => tracing::error!("Server connection ran into an error: {}", e),
                }
            });
            return Ok(());
        }
    }
}

pub fn startup_server(
    runtime: &tokio::runtime::Runtime,
    cloud_sender: broadcast::Sender<PointCloud>,
    cancel_sender: broadcast::Sender<ConduitMessage>,
    listener_port: String,
) -> JoinHandle<()> {
    let rt_handle = runtime.handle().clone();
    let this_cloud = cloud_sender.clone();
    let mut this_cancel = cancel_sender.clone();
    let mut server_cancel = this_cancel.subscribe();
    return runtime.spawn(async move {
        let mut server = match Server::new(listener_port, this_cloud, rt_handle).await {
            Ok(s) => s,
            Err(e) => {
                tracing::error!("Failed to start server: {}", e);
                return;
            }
        };

        match server.run(&mut server_cancel, &mut this_cancel).await {
            Ok(()) => (),
            Err(e) => tracing::error!("Server encountered an error: {}", e),
        }
    });
}
