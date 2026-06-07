#!/usr/bin/env bash
# download_vendor.sh — Download CDN vendor files for offline use
# Run this once after cloning the repo to populate static/vendor/
# Usage: bash scripts/download_vendor.sh

set -euo pipefail

VENDOR_DIR="$(cd "$(dirname "$0")/../static/vendor" && pwd)"
echo "Downloading vendor files to $VENDOR_DIR"

download() {
  local url="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [ ! -f "$dest" ]; then
    echo "  Downloading $url"
    curl -sfL "$url" -o "$dest" || echo "  WARNING: Failed to download $url"
  else
    echo "  Already exists: $dest"
  fi
}

# Font Awesome 6.5.1
FA_URL="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1"
download "$FA_URL/css/all.min.css" "$VENDOR_DIR/fontawesome/css/all.min.css"
download "$FA_URL/webfonts/fa-solid-900.woff2" "$VENDOR_DIR/fontawesome/webfonts/fa-solid-900.woff2"
download "$FA_URL/webfonts/fa-regular-400.woff2" "$VENDOR_DIR/fontawesome/webfonts/fa-regular-400.woff2"
download "$FA_URL/webfonts/fa-brands-400.woff2" "$VENDOR_DIR/fontawesome/webfonts/fa-brands-400.woff2"

# Chart.js 4.4.7
CHART_URL="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist"
download "$CHART_URL/chart.umd.min.js" "$VENDOR_DIR/chart.js/dist/chart.umd.min.js"

# html2canvas
H2C_URL="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist"
download "$H2C_URL/html2canvas.min.js" "$VENDOR_DIR/html2canvas/dist/html2canvas.min.js"

# HTMX 1.9.12
HTMX_URL="https://unpkg.com/htmx.org@1.9.12"
download "$HTMX_URL/dist/htmx.min.js" "$VENDOR_DIR/htmx.org/dist/htmx.min.js"

# Cropper.js 1.6.2
CROP_URL="https://cdn.jsdelivr.net/npm/cropperjs@1.6.2/dist"
download "$CROP_URL/cropper.min.js" "$VENDOR_DIR/cropperjs/dist/cropper.min.js"
download "$CROP_URL/cropper.min.css" "$VENDOR_DIR/cropperjs/dist/cropper.min.css"

echo "Done! Vendor files downloaded to $VENDOR_DIR"
