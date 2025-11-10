const fastify = require('fastify')({ logger: true });

const port = 8080;

fastify.get('/health', async (request, reply) => {
  return { service: 'push_service' };
});

const start = async () => {
  try {
    await fastify.listen({ port, host: '0.0.0.0' });
    console.log(`Push service listening on port ${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
