#!/usr/bin/env node
"use strict";

var net = require("net");

var opts = { address: "0.0.0.0", port: 8080 };

for (var i = 1; i < process.argv.length; i++) {
    var m = process.argv[i].match(/^(.*?)=(.*)$/);
    if (m) {
        opts[m[1]] = m[2];
    }
}

var server = net.createServer(function (socket) {
    socket.on("data", function (chunk) {
        // Check if we got start line and headers (no body support)
        if (chunk.indexOf("\x0d\x0a\x0d\x0a") >= 0) {
            var keepalive =
                chunk.indexOf("\x0d\x0aConnection: Keep-Alive\x0d\x0a") >= 0;

            // Write a minimal HTTP response
            // (the "Hello World!" message has been optimized away!)
            socket.write(
                "HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a" +
                    (keepalive ? "Connection: keep-alive\x0d\x0a" : "") +
                    "\x0d\x0a",
            );

            if (!keepalive) {
                socket.destroy();
            }
        }
    });
});

server.listen(opts.port, opts.address);
