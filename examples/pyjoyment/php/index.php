<?php
// The script of the directory, and of every path under the mount when it is the only one, as a front controller is
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
