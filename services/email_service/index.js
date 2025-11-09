const amqp = require('amqplib');
const nodemailer = require('nodemailer');

async function main() {
  const connection = await amqp.connect('amqp://admin:admin@localhost');
  const channel = await connection.createChannel();

  const queue = 'email.queue';
  await channel.assertQueue(queue, { durable: true });

  console.log(`Waiting for messages in ${queue}`);

  channel.consume(queue, async (msg) => {
    if (msg !== null) {
      const data = JSON.parse(msg.content.toString());
      console.log('Received:', data);

      // Send email logic here
      const transporter = nodemailer.createTransporter({
        service: 'gmail',
        auth: {
          user: 'your-email@gmail.com',
          pass: 'your-password'
        }
      });

      const mailOptions = {
        from: 'your-email@gmail.com',
        to: 'recipient@example.com', // Get from user service
        subject: 'Notification',
        text: 'Hello from notification system!'
      };

      transporter.sendMail(mailOptions, (error, info) => {
        if (error) {
          console.log(error);
        } else {
          console.log('Email sent: ' + info.response);
        }
      });

      channel.ack(msg);
    }
  });
}

main().catch(console.error);
