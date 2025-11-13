<?php

/** @var \Laravel\Lumen\Routing\Router $router */

/*
|--------------------------------------------------------------------------
| Application Routes
|--------------------------------------------------------------------------
|
| Here is where you can register all of the routes for an application.
| It is a breeze. Simply tell Lumen the URIs it should respond to
| and give it the Closure to call when that URI is requested.
|
*/

$router->get('/', function () use ($router) {
    return response()->json([
        'message' => 'Template Service is running 🚀',
        'lumen_version' => app()->version(),
    ]);
});

$router->get('/health', function () use ($router) {
    try {
        // Check Redis connection
        $redis = new Redis();
        $redis->connect(getenv('REDIS_HOST') ?: 'redis', getenv('REDIS_PORT') ?: 6379);
        $redis->ping();
        $redisStatus = 'connected';
    } catch (Exception $e) {
        $redisStatus = 'disconnected';
    }

    // Check database connection
    try {
        \Illuminate\Support\Facades\DB::connection()->getPdo();
        $dbStatus = 'connected';
    } catch (\Exception $e) {
        $dbStatus = 'disconnected';
    }

    // Check RabbitMQ connection (simplified check)
    $rabbitmqStatus = 'unknown'; // Could implement actual check if needed

    $status = ($redisStatus === 'connected' && $dbStatus === 'connected') ? 'healthy' : 'unhealthy';

    return response()->json([
        'status' => $status,
        'service' => 'template-service',
        'timestamp' => date('c'),
        'dependencies' => [
            'redis' => $redisStatus,
            'database' => $dbStatus,
            'rabbitmq' => $rabbitmqStatus,
        ],
    ]);
});

// Template CRUD routes
$router->group(['prefix' => 'api/templates'], function () use ($router) {
    $router->get('/', 'TemplateController@index');
    $router->post('/', 'TemplateController@store');
    $router->get('/{templateCode}', 'TemplateController@show');
    $router->put('/{templateCode}', 'TemplateController@update');
    $router->delete('/{templateCode}', 'TemplateController@destroy');
    $router->post('/{templateCode}/render', 'TemplateController@render');
});
