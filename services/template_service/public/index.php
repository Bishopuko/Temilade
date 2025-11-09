<?php
require __DIR__ . '/../vendor/autoload.php';

use Slim\Factory\AppFactory;

$app = AppFactory::create();

$app->get('/health', function ($request, $response, $args) {
    $response->getBody()->write("Healthy");
    return $response;
});

$app->get('/templates/{id}', function ($request, $response, $args) {
    $id = $args['id'];
    // Fetch template from DB
    $template = ['id' => $id, 'content' => 'Hello {{name}}!'];
    $response->getBody()->write(json_encode($template));
    return $response->withHeader('Content-Type', 'application/json');
});

$app->run();
?>
