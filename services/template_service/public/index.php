<?php
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'GET' && $_SERVER['REQUEST_URI'] === '/health') {
    try {
        // Check Redis connection
        $redis = new Redis();
        $redis->connect(getenv('REDIS_HOST') ?: 'redis', getenv('REDIS_PORT') ?: 6379);
        $redis->ping();
        $redisStatus = 'connected';
    } catch (Exception $e) {
        $redisStatus = 'disconnected';
    }

    // Check database connection (if needed)
    $dbStatus = 'not_configured'; // Template service might not need DB

    // Check RabbitMQ connection (simplified check)
    $rabbitmqStatus = 'unknown'; // Could implement actual check if needed

    $status = ($redisStatus === 'connected') ? 'healthy' : 'unhealthy';

    echo json_encode([
        'status' => $status,
        'service' => 'template-service',
        'timestamp' => date('c'),
        'dependencies' => [
            'redis' => $redisStatus,
            'database' => $dbStatus,
            'rabbitmq' => $rabbitmqStatus
        ]
    ]);
    exit;
}

echo json_encode(['error' => 'Not found']);
http_response_code(404);
