"""Verifica el punto de partida del Laboratorio 2 sin generar salidas.

Comprueba que el original coincide con la referencia confiable, que hay 12
pedidos, que DATAOPS_KEY está cargada y es la clave de .secrets/fernet.key,
que cifrar y descifrar funcionan (TODO 3 y 4) y que autorizar respeta la
matriz de permisos (TODO 2). Nunca muestra la clave ni datos personales.

Uso:
    python comprobar_preparacion_lab2.py [--base CARPETA]

Sin --base se usa la carpeta del repositorio (comportamiento original). Con
--base se usan CARPETA/datos, CARPETA/referencia.sha256 y
CARPETA/.secrets/fernet.key.

Códigos de salida: 0 si la preparación es correcta y 1 si hay que revisarla.
"""
import argparse
import hashlib
import os
import sys
from pathlib import Path

PERMISOS_ESPERADOS = {
    'operador': {'ejecutar', 'recuperar'},
    'analista': {'resumen'},
    'auditor': {'evidencias'},
}
ROLES = ['operador', 'analista', 'auditor', 'desconocido']
OPERACIONES = ['ejecutar', 'recuperar', 'resumen', 'evidencias', 'inexistente']


def exigir(condicion, mensaje):
    """Lanza AssertionError con el mensaje si la condición no se cumple.

    A diferencia de assert, la comprobación se mantiene con python -O.
    """
    if not condicion:
        raise AssertionError(mensaje)


class ComprobadorPreparacion:
    """Comprueba datos, referencia, clave y TODO 1 a 4 sobre una carpeta base."""

    def __init__(self, lab1, base=None):
        """Define las rutas de datos, referencia y clave.

        Argumentos:
            lab1: módulo lab1 ya importado.
            base: carpeta del entorno; por omisión, la del módulo lab1.
        """
        self.lab1 = lab1
        self.base = lab1.BASE if base is None else Path(base)
        self.datos = lab1.DATOS if base is None else self.base / 'datos'
        self.entrada = self.datos / 'pedidos.csv'
        self.referencia = self.base / 'referencia.sha256'
        self.clave = self.base / '.secrets' / 'fernet.key'

    def comprobar_datos(self):
        """Comprueba la huella del original, TODO 1 y el número de pedidos.

        Devuelve:
            Huella esperada de la referencia.
        """
        esperado = self.referencia.read_text(encoding='ascii').strip()
        real = hashlib.sha256(self.entrada.read_bytes()).hexdigest()
        exigir(real == esperado, 'El original no coincide; no recalcules la referencia')
        exigir(self.lab1.calcular_hash(self.entrada) == esperado, 'Revisa TODO 1')
        filas = self.lab1.leer_pedidos(self.entrada)
        exigir(len(filas) == 12, 'Se esperan 12 pedidos del caso')
        return esperado

    def comprobar_clave(self):
        """Comprueba la clave cargada y el cifrado de ida y vuelta (TODO 3 y 4)."""
        exigir(os.environ.get('DATAOPS_KEY'), 'Carga DATAOPS_KEY en esta terminal')
        clave = self.clave.read_text(encoding='ascii').strip()
        exigir(os.environ['DATAOPS_KEY'] == clave,
               'Carga la clave original de .secrets/fernet.key')
        fernet = self.lab1.cargar_cifrador()
        texto = 'prueba_sin_datos_personales'
        token = self.lab1.cifrar(texto, fernet)
        exigir(isinstance(token, str) and token != texto, 'Revisa TODO 3')
        exigir(self.lab1.descifrar(token, fernet) == texto, 'Revisa TODO 4')

    def comprobar_permisos(self):
        """Comprueba las 20 combinaciones de rol y operación (TODO 2)."""
        for rol in ROLES:
            permitidas = PERMISOS_ESPERADOS.get(rol, set())
            for operacion in OPERACIONES:
                try:
                    self.lab1.autorizar(rol, operacion)
                except PermissionError:
                    exigir(operacion not in permitidas, 'Permiso valido denegado')
                else:
                    exigir(operacion in permitidas,
                           'Operacion no autorizada permitida')

    def comprobar_copia(self, esperado):
        """Avisa si falta la copia alterada y, si existe, exige que difiera."""
        copia = self.datos / 'pedidos_prueba_parte1.csv'
        if not copia.exists():
            print('AVISO: falta la copia alterada; creala con comprobar_1a.py '
                  'antes del escenario A')
        else:
            exigir(hashlib.sha256(copia.read_bytes()).hexdigest() != esperado,
                   'La copia no esta alterada')

    def comprobar(self):
        """Ejecuta todas las comprobaciones e imprime el resultado final.

        Lanza:
            AssertionError: si alguna comprobación falla.
            OSError: si falta un archivo de la preparación.
            ValueError: si la clave o el contrato de datos no son válidos.
        """
        esperado = self.comprobar_datos()
        self.comprobar_clave()
        self.comprobar_permisos()
        self.comprobar_copia(esperado)
        print('Preparacion verificada: datos, referencia, clave y TODO 1 a 4')
        print('No se han creado salidas ni mostrado claves o datos personales')


def main(argv=None):
    """Interpreta --base y ejecuta el comprobador.

    Argumentos:
        argv: lista de argumentos; por omisión se usa sys.argv.

    Lanza:
        RuntimeError: si falta lab1.py o no está junto al comprobador.
    """
    parser = argparse.ArgumentParser(
        description='Verifica datos, referencia, clave y TODO 1 a 4')
    parser.add_argument('--base', type=Path, default=None,
                        help='carpeta base con datos/, referencia.sha256 y .secrets/')
    args = parser.parse_args(argv)
    try:
        import lab1
    except ImportError as exc:
        raise RuntimeError('Falta lab1.py o su dependencia; revisa README.md') from exc
    if Path(lab1.__file__).resolve().parent != Path(__file__).resolve().parent:
        raise RuntimeError('lab1.py debe estar junto a este comprobador')
    ComprobadorPreparacion(lab1, args.base).comprobar()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Mensajes sin imprimir excepciones que pudieran contener datos.
        if isinstance(exc, (AssertionError, RuntimeError, NotImplementedError)):
            sys.exit(f'REVISAR: {exc}')
        sys.exit(f'REVISAR: {type(exc).__name__}; consulta GUIA_PARTICIPANTE.md')
