use google_cloud_pubsub::client::{Client, ClientConfig};
use google_cloud_pubsub::subscription::SubscriptionConfig;
use google_cloud_gax::grpc::Status;
use std::time::Duration;
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() {
    let config = ClientConfig::default().with_auth().await.unwrap();
    dbg!(run(config).await.unwrap());
}

async fn run(config: ClientConfig) -> Result<(), Status> {

    // Create pubsub client.
    let client = Client::new(config).await.unwrap();

    // Get the topic to subscribe to.
    let topic = client.topic("Test_Topic");

    // Create subscription
    // If subscription name does not contain a "/", then the project is taken from client above. Otherwise, the
    // name will be treated as a fully qualified resource name
    let config = SubscriptionConfig {
        // Enable message ordering if needed (https://cloud.google.com/pubsub/docs/ordering)
        enable_message_ordering: true,
        ..Default::default()
    };

    // Create subscription
    let subscription = client.subscription("Test_Topic-sub");
    if !subscription.exists(None).await? {
        subscription.create(topic.fully_qualified_name(), config, None).await?;
    }

    // Token for cancel.
    let cancel = CancellationToken::new();
    let cancel2 = cancel.clone();
    tokio::spawn(async move {
        // Cancel after 60 seconds.
        tokio::time::sleep(Duration::from_secs(60)).await;
        cancel2.cancel();
    });

    // Receive blocks until the ctx is cancelled or an error occurs.
    // Or simply use the `subscription.subscribe` method.
    subscription.receive(|mut message, cancel| async move {
        // Handle data.
        println!("Got Message: {:?}", message.message.data);

        // Ack or Nack message.
        let _ = message.ack().await;
    }, cancel.clone(), None).await?;

    // Delete subscription if needed.
    subscription.delete(None).await?;

    Ok(())
}
