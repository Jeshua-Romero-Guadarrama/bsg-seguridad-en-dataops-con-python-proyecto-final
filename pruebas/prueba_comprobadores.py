"""Pruebas de comprobar_preparacion_lab2.py y comprobar_lab2.py por subprocess."""
import pytest

from pruebas.conftest import RAIZ, lanzar

PREPARACION = RAIZ / 'comprobar_preparacion_lab2.py'
COMPROBAR_LAB2 = RAIZ / 'comprobar_lab2.py'
LINEAS_PREPARACION = [
    'Preparacion verificada: datos, referencia, clave y TODO 1 a 4',
    'No se han creado salidas ni mostrado claves o datos personales',
]
MENSAJES_OK = {
    5: 'TODO 5 OK: tres eventos anexados con campos exactos y fecha UTC.',
    6: 'TODO 6 OK: resumen valido aceptado y ocho casos invalidos rechazados.',
    7: 'TODO 7 OK: traza valida aceptada y catorce casos invalidos '
       'rechazados.',
}
# lab2.py de prueba con los tres TODO pendientes, como en el material.
LAB2_PENDIENTE = '''\
def registrar_evento(ruta, run_id, rol, operacion, resultado):
    raise NotImplementedError('TODO 5: registrar_evento')


def comprobar_minimizacion(ruta):
    raise NotImplementedError('TODO 6: comprobar_minimizacion')


def comprobar_trazabilidad(ruta, run_id):
    raise NotImplementedError('TODO 7: comprobar_trazabilidad')
'''
# lab2.py de prueba con TODO 6 incorrecto: acepta cualquier archivo.
LAB2_PERMISIVO = LAB2_PENDIENTE.replace(
    "raise NotImplementedError('TODO 6: comprobar_minimizacion')",
    'return True')
# lab2.py de prueba con TODO 7 que lanza una excepcion ante bytes no UTF-8:
# delega en la solucion, pero antes lee el archivo sin capturar errores.
LAB2_EXCEPCION = 'import lab2_solucion\n\n\n' + LAB2_PENDIENTE.replace(
    "raise NotImplementedError('TODO 7: comprobar_trazabilidad')",
    "open(ruta, encoding='utf-8').read()\n"
    "    return lab2_solucion.comprobar_trazabilidad(ruta, run_id)")


class PruebaComprobadorPreparacion:
    """comprobar_preparacion_lab2.py con --base sobre un entorno temporal."""

    def lanzar_preparacion(self, entorno, variables):
        """Ejecuta el comprobador con --base en el entorno temporal."""
        return lanzar(PREPARACION, ['--base', entorno.base], variables,
                      entorno.base)

    def prueba_preparacion_verificada(self, entorno, entorno_proceso):
        """Con la copia alterada creada, solo imprime las dos líneas finales."""
        entorno.alterar_entrada()
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == LINEAS_PREPARACION

    def prueba_aviso_sin_copia(self, entorno, entorno_proceso):
        """Sin la copia alterada avisa y aun así verifica la preparación."""
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == [
            'AVISO: falta la copia alterada; creala con comprobar_1a.py '
            'antes del escenario A',
            *LINEAS_PREPARACION,
        ]

    def prueba_sin_salidas_ni_secretos(self, entorno, entorno_proceso):
        """No crea salidas ni ejecuciones y no muestra la clave."""
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 0, r.stderr
        clave = entorno.clave.read_text(encoding='ascii').strip()
        assert clave not in r.stdout + r.stderr
        assert not (entorno.base / 'salidas').exists()
        assert not (entorno.base / 'ejecuciones').exists()

    def prueba_sin_clave(self, entorno, entorno_proceso):
        """Sin DATAOPS_KEY pide cargarla con código 1."""
        entorno_proceso.pop('DATAOPS_KEY')
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 1
        assert r.stderr.strip() == 'REVISAR: Carga DATAOPS_KEY en esta terminal'

    def prueba_otra_clave(self, entorno, entorno_proceso):
        """Una clave distinta de .secrets/fernet.key se rechaza."""
        from cryptography.fernet import Fernet
        entorno_proceso['DATAOPS_KEY'] = Fernet.generate_key().decode()
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 1
        assert r.stderr.strip() == (
            'REVISAR: Carga la clave original de .secrets/fernet.key')

    def prueba_original_alterado(self, entorno, entorno_proceso):
        """Si el original cambia, se detiene sin recalcular la referencia."""
        referencia = entorno.referencia.read_bytes()
        entorno.entrada.write_bytes(entorno.entrada.read_bytes().replace(
            b'1850.00', b'1851.00', 1))
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 1
        assert r.stderr.strip() == (
            'REVISAR: El original no coincide; no recalcules la referencia')
        assert entorno.referencia.read_bytes() == referencia

    def prueba_copia_no_alterada(self, entorno, entorno_proceso):
        """Una copia idéntica al original no sirve como copia alterada."""
        copia = entorno.entrada.parent / 'pedidos_prueba_parte1.csv'
        copia.write_bytes(entorno.entrada.read_bytes())
        r = self.lanzar_preparacion(entorno, entorno_proceso)
        assert r.returncode == 1
        assert r.stderr.strip() == 'REVISAR: La copia no esta alterada'

    def prueba_sin_preparar(self, tmp_path, entorno_proceso):
        """Una carpeta sin preparar da REVISAR con el tipo de error."""
        r = lanzar(PREPARACION, ['--base', tmp_path / 'vacia'],
                   entorno_proceso, tmp_path)
        assert r.returncode == 1
        assert r.stderr.strip() == (
            'REVISAR: FileNotFoundError; consulta GUIA_PARTICIPANTE.md')


class PruebaComprobadorLab2:
    """comprobar_lab2.py sobre la solución y sobre versiones de prueba."""

    @pytest.mark.parametrize('todo', [5, 6, 7])
    def prueba_etapa_aislada(self, entorno_proceso, tmp_path, todo):
        """Cada --todo imprime su OK y la advertencia de etapa aislada."""
        r = lanzar(COMPROBAR_LAB2, ['--todo', todo], entorno_proceso, tmp_path)
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == [
            MENSAJES_OK[todo],
            f'Etapa TODO {todo} verificada; no valida las otras funciones.',
        ]

    def prueba_completa(self, entorno_proceso, tmp_path):
        """Sin --todo verifica 5, 6 y 7 en orden."""
        r = lanzar(COMPROBAR_LAB2, [], entorno_proceso, tmp_path)
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == [
            MENSAJES_OK[5], MENSAJES_OK[6], MENSAJES_OK[7],
            'TODO 5, 6 y 7 verificados. Continua con la auditoria completa.',
        ]

    def prueba_no_toca_el_repositorio(self, entorno_proceso, tmp_path):
        """No crea archivos ni carpetas nuevos en la raíz del repositorio."""
        ignorados = {'__pycache__', '.pytest_cache'}
        antes = sorted(p.name for p in RAIZ.iterdir()
                       if p.name not in ignorados)
        r = lanzar(COMPROBAR_LAB2, [], entorno_proceso, tmp_path)
        assert r.returncode == 0, r.stderr
        assert sorted(p.name for p in RAIZ.iterdir()
                      if p.name not in ignorados) == antes

    def prueba_todo_invalido(self, entorno_proceso, tmp_path):
        """Un --todo fuera de 5, 6 y 7 termina con código 2."""
        r = lanzar(COMPROBAR_LAB2, ['--todo', '4'], entorno_proceso, tmp_path)
        assert r.returncode == 2

    def preparar_copia(self, tmp_path, contenido):
        """Copia el comprobador junto a un lab2.py de prueba.

        También copia lab1.py y la solución como lab2_solucion.py para los
        lab2.py de prueba que delegan en ella.
        """
        (tmp_path / 'comprobar_lab2.py').write_bytes(
            COMPROBAR_LAB2.read_bytes())
        (tmp_path / 'lab1.py').write_bytes((RAIZ / 'lab1.py').read_bytes())
        (tmp_path / 'lab2_solucion.py').write_bytes(
            (RAIZ / 'lab2.py').read_bytes())
        (tmp_path / 'lab2.py').write_text(contenido, encoding='utf-8')
        return tmp_path / 'comprobar_lab2.py'

    @pytest.mark.parametrize('todo', [5, 6, 7])
    def prueba_pendiente(self, entorno_proceso, tmp_path, todo):
        """Un TODO sin implementar da PENDIENTE: TODO n con código 2."""
        script = self.preparar_copia(tmp_path, LAB2_PENDIENTE)
        r = lanzar(script, ['--todo', todo], entorno_proceso, tmp_path)
        assert r.returncode == 2
        assert r.stderr.strip() == (
            f'PENDIENTE: TODO {todo}; implementa y guarda esa funcion en '
            'lab2.py')
        assert 'OK' not in r.stdout

    def prueba_completa_se_detiene_en_el_primero(self, entorno_proceso,
                                                 tmp_path):
        """Sin --todo y todo pendiente, se detiene en TODO 5."""
        script = self.preparar_copia(tmp_path, LAB2_PENDIENTE)
        r = lanzar(script, [], entorno_proceso, tmp_path)
        assert r.returncode == 2
        assert r.stderr.startswith('PENDIENTE: TODO 5')

    def prueba_detecta_minimizacion_permisiva(self, entorno_proceso,
                                              tmp_path):
        """Una función que devuelve True siempre no pasa la etapa 6."""
        script = self.preparar_copia(tmp_path, LAB2_PERMISIVO)
        r = lanzar(script, ['--todo', '6'], entorno_proceso, tmp_path)
        assert r.returncode == 1
        assert r.stderr.startswith('REVISAR: TODO 6: rechaza')

    def prueba_detecta_excepcion(self, entorno_proceso, tmp_path):
        """Una excepción con un archivo inválido se informa con su tipo."""
        script = self.preparar_copia(tmp_path, LAB2_EXCEPCION)
        r = lanzar(script, ['--todo', '7'], entorno_proceso, tmp_path)
        assert r.returncode == 1
        assert r.stderr.strip() == (
            'REVISAR TODO 7: UnicodeDecodeError; comprueba el contrato de '
            'errores')
