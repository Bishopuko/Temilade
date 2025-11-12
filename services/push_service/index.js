const amqp = require("amqplib");
const redis = require("redis");
const admin = require("firebase-admin");

// Initialize Firebase Admin SDK
let firebaseInitialized = false;

if (process.env.FIREBASE_SERVICE_ACCOUNT) {
  // Initialize with service account JSON from environment variable
  try {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
    });
    firebaseInitialized = true;
    console.log("Firebase Admin SDK initialized with service account");
  } catch (error) {
    console.error(
      "Failed to initialize Firebase with service account:",
      error.message
    );
  }
} else {
  console.warn(
    "Firebase credentials not found. FCM notifications will not work."
  );
  console.warn(
    "Please set FIREBASE_SERVICE_ACCOUNT (JSON string) or FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, and FIREBASE_CLIENT_EMAIL"
  );
}

// Redis client
const redisClient = redis.createClient({
  socket: {
    host: process.env.REDIS_HOST || "redis",
    port: process.env.REDIS_PORT || 6379,
  },
});

redisClient.on("error", (err) => {
  console.error("Redis error:", err);
});

// Connect to Redis
redisClient.connect().catch((err) => {
  console.error("Redis connection error:", err);
});

// Connect to RabbitMQ
async function connectRabbitMQ() {
  try {
    const rabbitmqHost = process.env.RABBITMQ_HOST || "rabbitmq";
    const rabbitmqUser = process.env.RABBITMQ_USER || "admin";
    const rabbitmqPass = process.env.RABBITMQ_PASS || "admin";
    const rabbitmqUrl =
      process.env.RABBITMQ_URL ||
      `amqp://${rabbitmqUser}:${rabbitmqPass}@${rabbitmqHost}`;
    const connection = await amqp.connect(rabbitmqUrl);
    const channel = await connection.createChannel();

    // Declare exchange and queue
    await channel.assertExchange("notifications.direct", "direct", {
      durable: false,
    });
    await channel.assertQueue("push.queue", {
      durable: true,
      arguments: {
        "x-dead-letter-exchange": "notifications.dlx",
        "x-dead-letter-routing-key": "failed",
      },
    });
    await channel.bindQueue("push.queue", "notifications.direct", "push.queue");

    console.log("Push service connected to RabbitMQ");

    // Consume messages
    channel.consume("push.queue", async (msg) => {
      if (msg) {
        const message = JSON.parse(msg.content.toString());

        try {
          console.log("Message to process", message);

          console.log("Processing push notification:::", message.request_id);

          // Get user contact info
          const userResponse = await fetch(
            `http://user_service:5000/users/${message.user_id}/contact`
          );
          if (!userResponse.ok) {
            throw new Error("Failed to get user contact info");
          }
          const userData = await userResponse.json();

          // Get template
          const templateResponse = await fetch(
            `http://template_service:8081/templates/${message.template_code}`
          );
          if (!templateResponse.ok) {
            throw new Error("Failed to get template");
          }
          const templateData = await templateResponse.json();

          // Render push content
          let title = templateData.subject;
          let body = templateData.body;
          const userDeviceToken = userData.device_token;

          // let title = "TEST TITLE";
          // let body = "TEST BODY";
          // const userDeviceToken = "test_device_token";

          // Simple variable replacement
          Object.keys(message.variables).forEach((key) => {
            const regex = new RegExp(`{{${key}}}`, "g");
            title = title.replace(regex, message.variables[key]);
            body = body.replace(regex, message.variables[key]);
          });

          // Send push notification via FCM
          console.log(`Sending push to ${userDeviceToken}: ${title} - ${body}`);

          // Validate device token
          if (!userDeviceToken) {
            throw new Error("Invalid or missing device token");
          }

          // Check if Firebase is initialized
          if (!firebaseInitialized) {
            throw new Error(
              "Firebase Admin SDK not initialized. Please configure Firebase credentials."
            );
          }

          // Build FCM notification object
          const notification = {
            title: title,
            body: body,
          };

          // Add image if available
          if (message.image) {
            notification.imageUrl = message.image;
          }

          // Build data payload
          const dataPayload = {
            request_id: message.request_id,
            ...message.variables, // Include any additional variables as data
          };

          // Add click action/link if available
          if (message.link) {
            dataPayload.click_action = message.link;
          }

          // Send FCM notification
          const fcmMessage = {
            notification: notification,
            data: dataPayload,
            token: userDeviceToken,
          };

          const response = await admin.messaging().send(fcmMessage);
          // try {
          //   const response = await admin.messaging().send(fcmMessage);
          //   console.log("FCM notification sent successfully:", response);
          //   console.log("Push sent successfully:", message.request_id);
          // } catch (fcmError) {
          //   // Handle FCM-specific errors
          //   if (
          //     fcmError.code === "messaging/invalid-registration-token" ||
          //     fcmError.code === "messaging/registration-token-not-registered"
          //   ) {
          //     throw new Error(
          //       `Invalid or unregistered device token: ${fcmError.message}`
          //     );
          //   } else if (fcmError.code === "messaging/invalid-argument") {
          //     throw new Error(
          //       `Invalid FCM message format: ${fcmError.message}`
          //     );
          //   } else {
          //     throw new Error(`FCM send failed: ${fcmError.message}`);
          //   }
          // }

          // Update status to 'delivered' with structured data
          const statusData = {
            notification_id: message.request_id,
            status: "delivered",
            timestamp: new Date().toISOString(),
            error: null,
          };
          redisClient.setEx(
            `status:${message.request_id}`,
            3600,
            JSON.stringify(statusData)
          );

          channel.ack(msg);
        } catch (error) {
          console.error("Error processing push:", error);

          // Update status to 'failed' with error details
          const statusData = {
            notification_id: message.request_id,
            status: "failed",
            timestamp: new Date().toISOString(),
            error: error.message,
          };
          redisClient.setEx(
            `status:${message.request_id}`,
            3600,
            JSON.stringify(statusData)
          );

          channel.nack(msg, false, false); // Don't requeue
        }
      }
    });
  } catch (error) {
    console.error("RabbitMQ connection error:", error);
    setTimeout(connectRabbitMQ, 5000);
  }
}

connectRabbitMQ();
