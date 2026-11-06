"""Preparación del entorno del laboratorio de Comercial Nova.

Genera una sola vez el dataset ficticio de 12 pedidos, la referencia SHA-256
del original conocido y la clave Fernet local. Nunca reemplaza un entorno
existente y nunca muestra la clave.

Uso:
    python preparar.py
"""
import csv
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet

BASE = Path(__file__).resolve().parent
CAMPOS = [
    'pedido_id', 'cliente_id', 'nombre_cliente',
    'correo', 'ciudad', 'importe', 'estado',
]
# Todos los clientes y pedidos son ficticios.
# Numero de cliente, ciudad, importe y estado por pedido.
PEDIDOS = [
    (1, 'Villahermosa', '1850.00', 'Confirmado'),
    (2, 'Merida', '950.50', 'Confirmado'),
    (3, 'Puebla', '1200.00', 'Cancelado'),
    (1, 'Villahermosa', '650.00', 'Confirmado'),
    (4, 'Merida', '1499.50', 'Confirmado'),
    (5, 'Puebla', '2100.00', 'Confirmado'),
    (6, 'Villahermosa', '800.00', 'Cancelado'),
    (7, 'Puebla', '400.00', 'Confirmado'),
    (8, 'Merida', '300.00', 'Confirmado'),
    (9, 'Villahermosa', '1750.00', 'Confirmado'),
    (10, 'Puebla', '550.00', 'Cancelado'),
    (11, 'Merida', '1250.00', 'Confirmado'),
]


class PreparadorEntorno:
    """Crea el dataset, la referencia y la clave de un entorno de práctica.

    Todas las rutas se calculan a partir de una carpeta base, lo que permite
    preparar el entorno del repositorio o uno temporal para las pruebas.
    """

    def __init__(self, base: Path):
        """Calcula las rutas del entorno a partir de la carpeta base.

        Argumentos:
            base: carpeta donde se crearán datos/, .secrets/ y la referencia.
        """
        self.base = Path(base)
        self.datos = self.base / 'datos'
        self.secretos = self.base / '.secrets'
        self.entrada = self.datos / 'pedidos.csv'
        self.referencia = self.base / 'referencia.sha256'
        self.clave = self.secretos / 'fernet.key'

    @staticmethod
    def filas():
        """Construye las filas del dataset ficticio en el orden del contrato.

        Devuelve:
            Lista de diccionarios con las columnas de CAMPOS, una por pedido.
        """
        return [
            {
                'pedido_id': f'PED-{n}',
                'cliente_id': f'CLI-{cliente:03d}',
                'nombre_cliente': f'Cliente Prueba {cliente:03d}',
                'correo': f'cliente{cliente:03d}@example.com',
                'ciudad': ciudad,
                'importe': importe,
                'estado': estado,
            }
            for n, (cliente, ciudad, importe, estado) in enumerate(
                PEDIDOS, start=1001)
        ]

    def preparar(self):
        """Genera el entorno completo sin reemplazar archivos previos.

        Escribe el CSV original, registra su huella como referencia confiable
        y crea la clave Fernet con permisos restringidos cuando el sistema lo
        permite. La clave no se imprime.

        Lanza:
            FileExistsError: si ya existe la entrada, la referencia o la clave.
        """
        self.datos.mkdir(exist_ok=True)
        self.secretos.mkdir(exist_ok=True)
        if any(p.exists() for p in (self.entrada, self.referencia, self.clave)):
            raise FileExistsError('Entorno existente; revisar antes de recrear')
        with self.entrada.open('w', encoding='utf-8', newline='') as f:
            escritor = csv.DictWriter(f, fieldnames=CAMPOS)
            escritor.writeheader()
            escritor.writerows(self.filas())
        self.referencia.write_text(
            hashlib.sha256(self.entrada.read_bytes()).hexdigest(),
            encoding='ascii')
        with self.clave.open('xb') as f:
            f.write(Fernet.generate_key())
        try:
            self.clave.chmod(0o600)
        except OSError:
            pass  # En Windows se requiere gestionar ACL aparte.
        print('Dataset, referencia y clave creados sin mostrarlos')


def main():
    """Prepara el entorno en la carpeta del repositorio."""
    PreparadorEntorno(BASE).preparar()


if __name__ == '__main__':
    main()
