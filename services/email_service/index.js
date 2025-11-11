const amqp = require('amqplib');
const nodemailer = require('nodemailer');
const redis = require('redis');

// Redis client
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'redis',
  port: process.env.REDIS_PORT || 6379
});

redisClient.on('error', (err) => {
  console.error('Redis error:', err);
});

// Email transporter
const transporter = nodemailer.createTransporter({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: process.env.SMTP_PORT || 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  }
});

// Connect to RabbitMQ
async function connectRabbitMQ() {
  try {
    const connection = await amqp.connect(process.env.RABBITMQ_URL || 'amqp://rabbitmq');
    const channel = await connection.createChannel();

    // Declare exchange and queue
    await channel.assertExchange('notifications.direct', 'direct');
    await channel.assertQueue('email.queue');
    await channel.bindQueue('email.queue', 'notifications.direct', 'email.queue');

    console.log('Email service connected to RabbitMQ');

    // Consume messages
    channel.consume('email.queue', async (msg) => {
      if (msg) {
        try {
          const message = JSON.parse(msg.content.toString());
          console.log('Processing email notification:', message.request_id);

          // Get user contact info
          const userResponse = await fetch(`http://user_service:5000/users/${message.user_id}/contact`);
          if (!userResponse.ok) {
            throw new Error('Failed to get user contact info');
          }
          const userData = await userResponse.json();

          // Get template
          const templateResponse = await fetch(`http://template_service:8081/templates/${message.template_code}`);
          if (!templateResponse.ok) {
            throw new Error('Failed to get template');
          }
          const templateData = await templateResponse.json();

          // Render email content
          let subject = templateData.subject;
          let body = templateData.body;

          // Simple variable replacement
          Object.keys(message.variables).forEach(key => {
            const regex = new RegExp(`{{${key}}}`, 'g');
            subject = subject.replace(regex, message.variables[key]);
            body = body.replace(regex, message.variables[key]);
          });

          // Send email
          await transporter.sendMail({
            from: process.env.SMTP_USER,
            to: userData.email,
            subject: subject,
            html: body
          });

          console.log('Email sent successfully:', message.request_id);

          // Update status to 'delivered' with structured data
          const statusData = {
            notification_id: message.request_id,
            status: 'delivered',
            timestamp: new Date().toISOString(),
            error: null
          };
          redisClient.setex(`status:${message.request_id}`, 3600, JSON.stringify(statusData));

          channel.ack(msg);
        } catch (error) {
          console.error('Error processing email:', error);

          // Update status to 'failed' with error details
          const statusData = {
            notification_id: message.request_id,
            status: 'failed',
            timestamp: new Date().toISOString(),
            error: error.message
          };
          redisClient.setex(`status:${message.request_id}`, 3600, JSON.stringify(statusData));

          channel.nack(msg, false, false); // Don't requeue
        }
      }
    });

  } catch (error) {
    console.error('RabbitMQ connection error:', error);
    setTimeout(connectRabbitMQ, 5000);
  }
}

connectRabbitMQ();
