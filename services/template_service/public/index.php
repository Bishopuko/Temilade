<?php
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'GET' && $_SERVER['REQUEST_URI'] === '/health') {
    echo json_encode(['service' => 'template_service']);
    exit;
}

echo json_encode(['error' => 'Not found']);
http_response_code(404);
