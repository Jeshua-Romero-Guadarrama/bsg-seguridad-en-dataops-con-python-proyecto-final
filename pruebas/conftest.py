"""Fixtures compartidas: un entorno completo y aislado en tmp_path.

Cada prueba recibe datos, referencia y clave propios creados con
PreparadorEntorno; la clave se inyecta en DATAOPS_KEY con monkeypatch y nunca
se imprime. Las pruebas no dependen de datos/, .secrets/, referencia.sha256
ni ejecuciones/ del repositorio.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from lab2 import AuditorNova  # noqa: E402
from preparar import PreparadorEntorno  # noqa: E402

SCRIPTS = (
    'lab1.py', 'lab2.py', 'preparar.py', 'comprobar_1a.py',
    'comprobar_preparacion_lab2.py', 'comprobar_lab2.py',
)


@dataclass
class Entorno:
    """Rutas de un entorno de práctica temporal."""

    base: Path
    entrada: Path
    referencia: Path
    clave: Path
    salidas: Path
    ejecuciones: Path

    def alterar_entrada(self, nombre='pedidos_prueba_parte1.csv'):
        """Crea una copia de la entrada con 1850.00 cambiado por 1851.00.

        Argumentos:
            nombre: nombre del archivo de la copia dentro de datos/.

        Devuelve:
            Ruta de la copia alterada.
        """
        copia = self.entrada.parent / nombre
        contenido = self.entrada.read_bytes()
        alterado = contenido.replace(b'1850.00', b'1851.00', 1)
        assert alterado != contenido
        copia.write_bytes(alterado)
        return copia


def lanzar(script, argumentos, variables, cwd):
    """Ejecuta un script con el intérprete actual y devuelve el proceso.

    Argumentos:
        script: ruta del archivo .py.
        argumentos: lista de argumentos de línea de comandos.
        variables: variables de entorno del proceso hijo.
        cwd: carpeta de trabajo.
    """
    return subprocess.run(
        [sys.executable, str(script), *map(str, argumentos)],
        env=variables, cwd=cwd, capture_output=True, text=True,
        encoding='utf-8', timeout=120)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Prepara un entorno completo en tmp_path e inyecta DATAOPS_KEY."""
    preparador = PreparadorEntorno(tmp_path)
    with contextlib.redirect_stdout(io.StringIO()):
        preparador.preparar()
    clave = preparador.clave.read_text(encoding='ascii').strip()
    monkeypatch.setenv('DATAOPS_KEY', clave)
    return Entorno(
        base=tmp_path,
        entrada=preparador.entrada,
        referencia=preparador.referencia,
        clave=preparador.clave,
        salidas=tmp_path / 'salidas',
        ejecuciones=tmp_path / 'ejecuciones',
    )


@pytest.fixture
def entorno_proceso(entorno):
    """Variables de entorno para lanzar subprocesos con la clave cargada."""
    variables = dict(os.environ)
    variables['PYTHONIOENCODING'] = 'utf-8'
    return variables


@pytest.fixture
def proyecto(entorno):
    """Copia los scripts al entorno temporal y devuelve su carpeta.

    Así las rutas por omisión de lab2.py (datos/, referencia.sha256 y
    ejecuciones/) apuntan a tmp_path y nunca al repositorio.
    """
    for nombre in SCRIPTS:
        shutil.copy2(RAIZ / nombre, entorno.base / nombre)
    return entorno.base


@pytest.fixture
def auditor(entorno):
    """Auditor que crea sus ejecuciones dentro del entorno temporal."""
    return AuditorNova(entorno.ejecuciones)


@pytest.fixture
def ejecucion_valida(entorno, auditor):
    """Audita una ejecución válida como operador y devuelve su reporte."""
    return auditor.auditar('operador', entorno.entrada, entorno.referencia)
