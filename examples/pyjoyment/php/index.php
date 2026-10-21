<?php
// The script that php-fpm runs for every path under the mount, as a front controller does
if ($_SERVER['PATH_INFO'] === '/events') {
    header('Content-Type: text/event-stream');
    for ($n = 0; $n < 3; $n++) {
        echo "data: $n\n\n";
        flush();
    }
    exit;
}

header('Content-Type: text/plain');
echo "Hello PHP at {$_SERVER['SCRIPT_NAME']} for {$_SERVER['PATH_INFO']} ({$_SERVER['REQUEST_METHOD']} {$_SERVER['REQUEST_URI']})!\n";
