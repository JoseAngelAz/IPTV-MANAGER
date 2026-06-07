#!/usr/bin/env python
"""
Optimiza una imagen para usarla como background en la landing page.

Uso:
    python scripts/optimizar_bg.py ruta/de/mi_imagen.png

Salida:
    Crea static/img/bg.webp (WebP calidad 80%, max 1920px ancho)
    con el mínimo peso posible.

Requisitos:
    pip install Pillow
"""
import sys
import os
from pathlib import Path
from PIL import Image


def optimizar(origen, destino, max_width=1920, quality=80):
    img = Image.open(origen).convert('RGB')
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    img.save(destino, format='WEBP', quality=quality, optimize=True)
    peso_kb = os.path.getsize(destino) / 1024
    print(f'Optimizada: {destino} ({peso_kb:.1f} KB, {img.width}x{img.height})')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python scripts/optimizar_bg.py <imagen>')
        sys.exit(1)

    origen = Path(sys.argv[1])
    if not origen.exists():
        print(f'Error: no existe {origen}')
        sys.exit(1)

    destino = Path(__file__).parent.parent / 'static' / 'img' / 'bg.webp'
    destino.parent.mkdir(parents=True, exist_ok=True)
    optimizar(origen, destino)
