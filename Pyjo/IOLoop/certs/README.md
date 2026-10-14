# The default certificate for TLS servers

The certificate and key that a TLS server of `Pyjo.IOLoop.Server` uses when
it is given none, as `lib/Mojo/IOLoop/resources` in Mojolicious. They are not
secret and are meant for development only.

| Files                      | Certificate                                       |
| -------------------------- | ------------------------------------------------- |
| `ca.crt`                   | The CA that signs the server, `Pyjoyment Test CA` |
| `server.crt`, `server.key` | `localhost` and `127.0.0.1`, for a server         |

The key of the CA is not kept, so the certificate is made again with a new
CA. They are RSA 2048 keys, valid for a hundred years, made with OpenSSL 3 in
a temporary directory, from the root of the repository:

```sh
certs=$PWD/Pyjo/IOLoop/certs
cd "$(mktemp -d)"

openssl req -x509 -newkey rsa:2048 -nodes -days 36500 \
  -keyout ca.key -out ca.crt -subj '/O=Pyjoyment/CN=Pyjoyment Test CA' \
  -addext 'basicConstraints=critical,CA:TRUE' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign' \
  -addext 'subjectKeyIdentifier=hash'

openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj '/O=Pyjoyment/CN=localhost'
printf 'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid\n' > server.ext
openssl x509 -req -days 36500 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -extfile server.ext

openssl verify -CAfile ca.crt server.crt
```

Then copy the certificates and the key into `Pyjo/IOLoop/certs`, readable by
everyone, and delete the temporary directory, the key of the CA with it:

```sh
chmod 644 server.key
cp ca.crt server.crt server.key "$certs/"
cd "$certs" && rm -rf "$OLDPWD"
```
