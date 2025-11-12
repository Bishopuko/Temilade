const amqp = require("amqplib");
const nodemailer = require("nodemailer");
const redis = require("redis");

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

// Email transporter
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || "smtp.gmail.com",
  port: process.env.SMTP_PORT || 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
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

    // Declare exchange and queue with explicit options
    await channel.assertExchange("notifications.direct", "direct", {
      durable: false,
    });
    await channel.assertQueue("email.queue", {
      durable: true,
      arguments: {
        "x-dead-letter-exchange": "notifications.dlx",
        "x-dead-letter-routing-key": "failed",
      },
    });
    await channel.bindQueue(
      "email.queue",
      "notifications.direct",
      "email.queue"
    );

    console.log("Email service connected to RabbitMQ");

    // Consume messages
    channel.consume("email.queue", async (msg) => {
      if (msg) {
        let message = null;
        let requestId = "unknown";
        try {
          message = JSON.parse(msg.content.toString());
          console.log("Message to process", message);

          requestId = message.request_id || "unknown";
          console.log("Processing email notification:::", requestId);

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

          // Render email content
          let subject = templateData.subject;
          let body = templateData.body;
          const to = userData.email;

          // let subject = "TEST SUBJECT";
          // let body = "TEST BODY";
          // const to = "osuolaleabdullahi@gmail.com";

          // Simple variable replacement
          Object.keys(message.variables).forEach((key) => {
            const regex = new RegExp(`{{${key}}}`, "g");
            subject = subject.replace(regex, message.variables[key]);
            body = body.replace(regex, message.variables[key]);
          });

          // Send email
          await transporter.sendMail({
            from: process.env.SMTP_USER,
            to: to,
            subject: subject,
            html: body,
          });

          console.log("Email sent successfully:", message.request_id);

          // Update status to 'delivered' with structured data
          const statusData = {
            notification_id: message.request_id,
            status: "delivered",
            timestamp: new Date().toISOString(),
            error: null,
          };
          await redisClient.setEx(
            `status:${message.request_id}`,
            3600,
            JSON.stringify(statusData)
          );

          channel.ack(msg);
        } catch (error) {
          console.error("Error processing email:", error);

          // Update status to 'failed' with error details
          // Try to get request_id from message if available, otherwise use extracted requestId
          const failedRequestId = message?.request_id || requestId;
          const statusData = {
            notification_id: failedRequestId,
            status: "failed",
            timestamp: new Date().toISOString(),
            error: error.message,
          };
          await redisClient.setEx(
            `status:${failedRequestId}`,
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
