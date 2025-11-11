const amqp = require('amqplib');
const redis = require('redis');

// Redis client
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'redis',
  port: process.env.REDIS_PORT || 6379
});

redisClient.on('error', (err) => {
  console.error('Redis error:', err);
});

// Connect to RabbitMQ
async function connectRabbitMQ() {
  try {
    const connection = await amqp.connect(process.env.RABBITMQ_URL || 'amqp://rabbitmq');
    const channel = await connection.createChannel();

    // Declare exchange and queue
    await channel.assertExchange('notifications.direct', 'direct');
    await channel.assertQueue('push.queue');
    await channel.bindQueue('push.queue', 'notifications.direct', 'push.queue');

    console.log('Push service connected to RabbitMQ');

    // Consume messages
    channel.consume('push.queue', async (msg) => {
      if (msg) {
        try {
          const message = JSON.parse(msg.content.toString());
          console.log('Processing push notification:', message.request_id);

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

          // Render push content
          let title = templateData.subject;
          let body = templateData.body;

          // Simple variable replacement
          Object.keys(message.variables).forEach(key => {
            const regex = new RegExp(`{{${key}}}`, 'g');
            title = title.replace(regex, message.variables[key]);
            body = body.replace(regex, message.variables[key]);
          });

          // Send push notification (mock implementation)
          console.log(`Sending push to ${userData.device_token}: ${title} - ${body}`);

          // Simulate push sending
          await new Promise(resolve => setTimeout(resolve, 100));

          console.log('Push sent successfully:', message.request_id);

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
          console.error('Error processing push:', error);

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
