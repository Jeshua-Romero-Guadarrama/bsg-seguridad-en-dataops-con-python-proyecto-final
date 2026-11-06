"""Pruebas de la línea de comandos de lab2.py por subprocess.

Los scripts se copian al entorno temporal (fixture proyecto), de modo que las
rutas por omisión de lab2.py (datos/pedidos.csv, referencia.sha256 y
ejecuciones/) apuntan a tmp_path y se prueban tal como las usa la guía.
"""
import json
import re

import pytest

from pruebas.conftest import lanzar

PATRON_REPORTE = re.compile(
    r'^Reporte generado: (?P<ruta>.+[\\/]ejecuciones[\\/](?P<run_id>[0-9a-f]{32})'
    r'[\\/]reporte\.json)$')


def lanzar_lab2(proyecto, variables, *argumentos):
    """Ejecuta la copia de lab2.py dentro del entorno temporal."""
    return lanzar(proyecto / 'lab2.py', argumentos, variables, proyecto)


def ruta_reporte(proceso):
    """Extrae la ruta del reporte de la salida de ejecutar."""
    coincidencia = PATRON_REPORTE.match(proceso.stdout.strip())
    assert coincidencia, proceso.stdout
    return coincidencia


def estados(proyecto, coincidencia):
    """Devuelve control -> estado del reporte indicado."""
    ruta = proyecto / 'ejecuciones' / coincidencia['run_id'] / 'reporte.json'
    reporte = json.loads(ruta.read_text(encoding='utf-8'))
    return {c['control']: c['estado'] for c in reporte['controles']}


@pytest.fixture
def ejecucion_cli(proyecto, entorno_proceso):
    """Ejecuta lab2.py ejecutar --rol operador y devuelve la coincidencia."""
    r = lanzar_lab2(proyecto, entorno_proceso, 'ejecutar', '--rol', 'operador')
    assert r.returncode == 0, r.stderr
    return ruta_reporte(r)


class PruebaInterfazEjecutar:
    """ejecutar crea ejecuciones/RUN_ID y termina con código 0."""

    def prueba_ejecucion_valida(self, proyecto, ejecucion_cli):
        """Solo imprime la ruta y los cinco controles son SATISFACTORIO."""
        assert set(estados(proyecto, ejecucion_cli).values()) == {
            'SATISFACTORIO'}
        carpeta = proyecto / 'ejecuciones' / ejecucion_cli['run_id']
        assert (carpeta / 'salidas' / 'resumen.csv').is_file()

    def prueba_escenario_a(self, proyecto, entorno, entorno_proceso):
        """Con la copia alterada el código es 0 y el reporte muestra el fallo."""
        entorno.alterar_entrada()
        r = lanzar_lab2(proyecto, entorno_proceso, 'ejecutar', '--rol',
                        'operador', '--entrada',
                        'datos/pedidos_prueba_parte1.csv')
        assert r.returncode == 0, r.stderr
        coincidencia = ruta_reporte(r)
        resultado = estados(proyecto, coincidencia)
        assert resultado['INTEGRIDAD'] == 'FALLIDO'
        assert resultado['EJECUCION'] == 'FALLIDO'
        carpeta = proyecto / 'ejecuciones' / coincidencia['run_id']
        assert not (carpeta / 'salidas').exists()

    def prueba_escenario_b(self, proyecto, entorno_proceso):
        """Como analista el código es 0 y se registra DENEGADO."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'ejecutar', '--rol',
                        'analista')
        assert r.returncode == 0, r.stderr
        coincidencia = ruta_reporte(r)
        resultado = estados(proyecto, coincidencia)
        assert resultado['AUTORIZACION_INICIAL'] == 'FALLIDO'
        carpeta = proyecto / 'ejecuciones' / coincidencia['run_id']
        evento = json.loads((carpeta / 'eventos.jsonl').read_text(
            encoding='utf-8'))
        assert evento['resultado'] == 'DENEGADO'

    def prueba_sin_clave(self, proyecto, entorno_proceso):
        """Sin DATAOPS_KEY el reporte registra EJECUCION FALLIDO."""
        entorno_proceso.pop('DATAOPS_KEY')
        r = lanzar_lab2(proyecto, entorno_proceso, 'ejecutar')
        assert r.returncode == 0, r.stderr
        coincidencia = ruta_reporte(r)
        assert estados(proyecto, coincidencia)['EJECUCION'] == 'FALLIDO'
        carpeta = proyecto / 'ejecuciones' / coincidencia['run_id']
        assert not (carpeta / 'salidas').exists()

    def prueba_consola_sin_secretos(self, proyecto, entorno, entorno_proceso):
        """La salida no contiene la clave, correos, nombres ni tokens."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'ejecutar')
        assert r.returncode == 0, r.stderr
        ruta_reporte(r)
        texto = r.stdout + r.stderr
        assert entorno.clave.read_text(encoding='ascii').strip() not in texto
        assert '@' not in texto
        assert 'Cliente Prueba' not in texto
        assert 'gAAAA' not in texto

    def prueba_accion_invalida(self, proyecto, entorno_proceso):
        """Una acción fuera de ejecutar y consultar termina con código 2."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'borrar')
        assert r.returncode == 2
        assert not (proyecto / 'ejecuciones').exists()


class PruebaInterfazConsultar:
    """consultar solo muestra el reporte al auditor."""

    def prueba_auditor(self, proyecto, entorno_proceso, ejecucion_cli):
        """El auditor ve el JSON completo del reporte."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol',
                        'auditor', '--reporte', ejecucion_cli['ruta'])
        assert r.returncode == 0, r.stderr
        reporte = json.loads(r.stdout)
        assert reporte['run_id'] == ejecucion_cli['run_id']
        assert len(reporte['controles']) == 5

    def prueba_ruta_relativa(self, proyecto, entorno_proceso, ejecucion_cli):
        """La ruta relativa de la guía funciona desde la carpeta del proyecto."""
        relativa = f"ejecuciones/{ejecucion_cli['run_id']}/reporte.json"
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol',
                        'auditor', '--reporte', relativa)
        assert r.returncode == 0, r.stderr

    @pytest.mark.parametrize('rol', ['analista', 'operador', 'desconocido'])
    def prueba_escenario_c(self, proyecto, entorno_proceso, ejecucion_cli,
                           rol):
        """PermissionError con código 1, sin reporte ni nueva ejecución."""
        antes = sorted((proyecto / 'ejecuciones').iterdir())
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol', rol,
                        '--reporte', ejecucion_cli['ruta'])
        assert r.returncode == 1
        assert r.stderr.startswith('BLOQUEADO: PermissionError')
        assert r.stdout == ''
        assert sorted((proyecto / 'ejecuciones').iterdir()) == antes

    def prueba_falta_reporte(self, proyecto, entorno_proceso):
        """El auditor sin --reporte recibe un error de uso con código 2."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol',
                        'auditor')
        assert r.returncode == 2
        assert 'consultar requiere --reporte RUTA' in r.stderr

    def prueba_permiso_antes_que_reporte(self, proyecto, entorno_proceso):
        """El analista sin --reporte recibe primero PermissionError."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol',
                        'analista')
        assert r.returncode == 1
        assert r.stderr.startswith('BLOQUEADO: PermissionError')

    def prueba_no_lee_la_clave(self, proyecto, entorno, entorno_proceso):
        """--reporte no sirve para mostrar .secrets/fernet.key."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol',
                        'auditor', '--reporte', '.secrets/fernet.key')
        assert r.returncode == 1
        assert r.stderr.startswith('BLOQUEADO: ValueError')
        clave = entorno.clave.read_text(encoding='ascii').strip()
        assert clave not in r.stdout + r.stderr

    def prueba_reporte_inexistente(self, proyecto, entorno_proceso):
        """Un reporte que no existe termina con código 1 sin traceback."""
        r = lanzar_lab2(proyecto, entorno_proceso, 'consultar', '--rol',
                        'auditor', '--reporte', 'ejecuciones/RUN_ID/reporte.json')
        assert r.returncode == 1
        assert r.stderr.startswith('BLOQUEADO: FileNotFoundError')
        assert 'Traceback' not in r.stderr
