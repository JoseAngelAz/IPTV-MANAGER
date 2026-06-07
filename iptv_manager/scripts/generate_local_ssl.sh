#!/bin/sh
set -e

CERT_DIR="$(cd "$(dirname "$0")/../nginx/certs" && pwd)"
mkdir -p "$CERT_DIR"

docker run --rm -v "$CERT_DIR":/certs alpine:3.18 sh -c "apk add --no-cache openssl >/dev/null 2>&1 && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /certs/localhost.key \
  -out /certs/localhost.crt \
  -subj '/CN=localhost' \
  -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1'"

echo "Created localhost.crt and localhost.key in $CERT_DIR"
