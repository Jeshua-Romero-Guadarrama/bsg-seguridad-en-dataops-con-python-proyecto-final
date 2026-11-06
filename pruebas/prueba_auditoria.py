"""Pruebas de AuditorNova: ejecución válida, escenarios A, B y C y reporte."""
import csv
import json
from datetime import datetime, timezone

import pytest

import lab2
from lab2 import (AuditorNova, CONTROLES_PREVISTOS, ReporteAuditoria,
                  VerificadorTrazabilidad)

RESUMEN_ESPERADO = [
    ['ciudad', 'total_ventas'],
    ['Merida', '4000.00'],
    ['Puebla', '2500.00'],
    ['Villahermosa', '4250.00'],
]
EVENTOS_VALIDOS = [
    ('operador', 'ejecutar', 'PERMITIDO'),
    ('operador', 'pipeline', 'COMPLETADO'),
    ('analista', 'ejecutar', 'DENEGADO'),
]


def leer_reporte(ruta):
    """Devuelve el reporte JSON como diccionario."""
    return json.loads(ruta.read_text(encoding='utf-8'))


def estados(reporte):
    """Devuelve un diccionario control -> estado del reporte."""
    return {c['control']: c['estado'] for c in reporte['controles']}


def leer_eventos(ruta):
    """Devuelve los eventos de un JSONL."""
    return [json.loads(linea) for linea in
            ruta.read_text(encoding='utf-8').splitlines()]


class PruebaAuditoriaValida:
    """Operador con entrada original: cinco controles SATISFACTORIO."""

    def prueba_cinco_controles_satisfactorios(self, ejecucion_valida):
        """El reporte tiene solo los cinco controles y todos pasan."""
        reporte = leer_reporte(ejecucion_valida)
        assert [c['control'] for c in reporte['controles']] == list(
            CONTROLES_PREVISTOS)
        assert set(estados(reporte).values()) == {'SATISFACTORIO'}

    def prueba_campos_del_reporte(self, entorno, ejecucion_valida):
        """run_id, fecha UTC, rol y hash_entrada son correctos."""
        reporte = leer_reporte(ejecucion_valida)
        assert list(reporte) == ['run_id', 'fecha_utc', 'rol_ejecutor',
                                 'hash_entrada', 'controles']
        assert reporte['run_id'] == ejecucion_valida.parent.name
        assert len(reporte['run_id']) == 32
        assert reporte['rol_ejecutor'] == 'operador'
        assert reporte['hash_entrada'] == (
            entorno.referencia.read_text().strip())
        fecha = datetime.fromisoformat(reporte['fecha_utc'])
        assert fecha.utcoffset().total_seconds() == 0

    def prueba_estructura_de_la_carpeta(self, entorno, ejecucion_valida):
        """La ejecución vive en ejecuciones/RUN_ID con sus cuatro archivos."""
        carpeta = ejecucion_valida.parent
        assert carpeta.parent == entorno.ejecuciones
        archivos = sorted(p.relative_to(carpeta).as_posix()
                          for p in carpeta.rglob('*') if p.is_file())
        assert archivos == [
            'eventos.jsonl', 'reporte.json',
            'salidas/detalle_protegido.csv', 'salidas/resumen.csv',
        ]

    def prueba_tres_eventos(self, ejecucion_valida):
        """eventos.jsonl tiene los tres eventos con el run_id del reporte."""
        carpeta = ejecucion_valida.parent
        eventos = leer_eventos(carpeta / 'eventos.jsonl')
        assert [(e['rol'], e['operacion'], e['resultado'])
                for e in eventos] == EVENTOS_VALIDOS
        assert {e['run_id'] for e in eventos} == {carpeta.name}
        assert VerificadorTrazabilidad().verificar(
            carpeta / 'eventos.jsonl', carpeta.name) is True

    def prueba_salidas(self, ejecucion_valida):
        """Detalle con 12 filas cifradas y resumen con tres ciudades."""
        salidas = ejecucion_valida.parent / 'salidas'
        with (salidas / 'detalle_protegido.csv').open(
                encoding='utf-8', newline='') as f:
            filas = list(csv.DictReader(f))
        assert len(filas) == 12
        assert all(f['correo'].startswith('gAAAA') for f in filas)
        with (salidas / 'resumen.csv').open(encoding='utf-8',
                                            newline='') as f:
            assert list(csv.reader(f)) == RESUMEN_ESPERADO

    def prueba_sin_datos_personales_ni_clave(self, entorno, ejecucion_valida):
        """Reporte y eventos no contienen correos, nombres, tokens ni clave."""
        carpeta = ejecucion_valida.parent
        clave = entorno.clave.read_text(encoding='ascii').strip()
        for nombre in ('reporte.json', 'eventos.jsonl'):
            texto = (carpeta / nombre).read_text(encoding='utf-8')
            assert '@' not in texto
            assert 'Cliente Prueba' not in texto
            assert 'gAAAA' not in texto
            assert clave not in texto

    def prueba_consola_solo_muestra_la_ruta(self, entorno, capsys):
        """La consola muestra Reporte generado y la ruta, nada más."""
        ruta = AuditorNova(entorno.ejecuciones).auditar(
            'operador', entorno.entrada, entorno.referencia)
        salida = capsys.readouterr()
        assert salida.out == f'Reporte generado: {ruta}\n'
        assert salida.err == ''

    def prueba_funcion_de_modulo(self, entorno, monkeypatch):
        """lab2.auditar usa EJECUCIONES y conserva el contrato."""
        monkeypatch.setattr(lab2, 'EJECUCIONES', entorno.ejecuciones)
        ruta = lab2.auditar('operador', entorno.entrada, entorno.referencia)
        assert ruta.parent.parent == entorno.ejecuciones
        assert set(estados(leer_reporte(ruta)).values()) == {'SATISFACTORIO'}

    def prueba_reloj_inyectado(self, entorno):
        """Con un reloj fijo, eventos y reporte llevan esa fecha."""
        fecha = datetime(2026, 10, 29, 21, 30, tzinfo=timezone.utc)
        ruta = AuditorNova(entorno.ejecuciones, reloj=lambda: fecha).auditar(
            'operador', entorno.entrada, entorno.referencia)
        assert leer_reporte(ruta)['fecha_utc'] == fecha.isoformat()
        eventos = leer_eventos(ruta.parent / 'eventos.jsonl')
        assert {e['fecha_utc'] for e in eventos} == {fecha.isoformat()}


class PruebaEscenarioA:
    """Entrada alterada: falla la integridad y no se procesa nada."""

    @pytest.fixture
    def reporte_a(self, entorno, auditor):
        """Audita la copia alterada y devuelve la ruta del reporte."""
        return auditor.auditar('operador', entorno.alterar_entrada(),
                               entorno.referencia)

    def prueba_estados(self, reporte_a):
        """INTEGRIDAD y EJECUCION FALLIDO; los otros cuatro NO_EVALUADO."""
        assert estados(leer_reporte(reporte_a)) == {
            'INTEGRIDAD': 'FALLIDO',
            'EJECUCION': 'FALLIDO',
            'CIFRADO': 'NO_EVALUADO',
            'MINIMIZACION': 'NO_EVALUADO',
            'ACCESO_DENEGADO': 'NO_EVALUADO',
            'TRAZABILIDAD': 'NO_EVALUADO',
        }

    def prueba_sin_salidas_ni_huella(self, reporte_a):
        """Se conserva el reporte, sin salidas y sin hash_entrada."""
        carpeta = reporte_a.parent
        assert not (carpeta / 'salidas').exists()
        assert leer_reporte(reporte_a)['hash_entrada'] is None

    def prueba_evidencia_de_la_ejecucion(self, reporte_a):
        """EJECUCION indica ValueError y solo hay un evento PERMITIDO."""
        controles = {c['control']: c for c in
                     leer_reporte(reporte_a)['controles']}
        assert controles['EJECUCION']['evidencia'] == 'ValueError'
        assert controles['INTEGRIDAD']['accion'] == (
            'Revisar origen del archivo; no procesar')
        eventos = leer_eventos(reporte_a.parent / 'eventos.jsonl')
        assert [(e['rol'], e['operacion'], e['resultado'])
                for e in eventos] == [EVENTOS_VALIDOS[0]]

    def prueba_referencia_intacta(self, entorno, reporte_a):
        """La referencia no se recalcula para aceptar la copia."""
        from lab1 import calcular_hash
        assert calcular_hash(entorno.entrada) == (
            entorno.referencia.read_text().strip())


class PruebaEscenarioB:
    """Rol sin permiso: se registra DENEGADO y no se procesa nada."""

    @pytest.fixture
    def reporte_b(self, entorno, auditor):
        """Audita como analista y devuelve la ruta del reporte."""
        return auditor.auditar('analista', entorno.entrada,
                               entorno.referencia)

    def prueba_estados(self, reporte_b):
        """AUTORIZACION_INICIAL y EJECUCION FALLIDO; cinco NO_EVALUADO."""
        assert estados(leer_reporte(reporte_b)) == {
            'AUTORIZACION_INICIAL': 'FALLIDO',
            'EJECUCION': 'FALLIDO',
            **{nombre: 'NO_EVALUADO' for nombre in CONTROLES_PREVISTOS},
        }

    def prueba_evento_denegado(self, reporte_b):
        """El único evento es ejecutar DENEGADO para el analista."""
        carpeta = reporte_b.parent
        eventos = leer_eventos(carpeta / 'eventos.jsonl')
        assert [(e['run_id'], e['rol'], e['operacion'], e['resultado'])
                for e in eventos] == [
            (carpeta.name, 'analista', 'ejecutar', 'DENEGADO')]

    def prueba_sin_salidas_ni_huella(self, reporte_b):
        """No hay salidas ni se declara verificada la integridad."""
        assert not (reporte_b.parent / 'salidas').exists()
        reporte = leer_reporte(reporte_b)
        assert reporte['hash_entrada'] is None
        assert reporte['rol_ejecutor'] == 'analista'

    @pytest.mark.parametrize('rol', ['auditor', 'desconocido'])
    def prueba_otros_roles(self, entorno, auditor, rol):
        """Auditor y rol desconocido tampoco ejecutan."""
        ruta = auditor.auditar(rol, entorno.entrada, entorno.referencia)
        assert estados(leer_reporte(ruta))['AUTORIZACION_INICIAL'] == 'FALLIDO'
        assert not (ruta.parent / 'salidas').exists()

    def prueba_rol_en_blanco(self, entorno, auditor):
        """Un rol en blanco no deja evento y el reporte lo dice."""
        ruta = auditor.auditar('   ', entorno.entrada, entorno.referencia)
        reporte = leer_reporte(ruta)
        assert estados(reporte) == {
            'AUTORIZACION_INICIAL': 'FALLIDO',
            'EJECUCION': 'FALLIDO',
            **{nombre: 'NO_EVALUADO' for nombre in CONTROLES_PREVISTOS},
        }
        controles = {c['control']: c for c in reporte['controles']}
        assert controles['EJECUCION']['evidencia'] == 'PermissionError'
        assert (controles['AUTORIZACION_INICIAL']['evidencia']
                == 'Rol vacio; denegacion sin evento')
        assert not (ruta.parent / 'eventos.jsonl').exists()
        assert not (ruta.parent / 'salidas').exists()


class PruebaEscenarioC:
    """Consulta del reporte: solo el auditor puede verlo."""

    def prueba_auditor_consulta(self, auditor, ejecucion_valida):
        """El auditor obtiene el texto exacto del reporte."""
        texto = auditor.consultar('auditor', ejecucion_valida)
        assert texto == ejecucion_valida.read_text(encoding='utf-8')

    @pytest.mark.parametrize('rol', ['analista', 'operador', 'desconocido'])
    def prueba_otros_roles_denegados(self, entorno, auditor,
                                     ejecucion_valida, rol):
        """PermissionError antes de leer y sin crear otra ejecución."""
        antes = sorted(entorno.ejecuciones.iterdir())
        with pytest.raises(PermissionError) as error:
            auditor.consultar(rol, ejecucion_valida)
        assert '@' not in str(error.value)
        assert sorted(entorno.ejecuciones.iterdir()) == antes

    @pytest.mark.parametrize('relativa', [
        '.secrets/fernet.key', 'datos/pedidos.csv', 'referencia.sha256'])
    def prueba_solo_reportes_de_ejecuciones(self, entorno, auditor,
                                            relativa):
        """El auditor no puede leer la clave ni los datos con --reporte."""
        with pytest.raises(ValueError, match='Solo se consultan reportes'):
            auditor.consultar('auditor', entorno.base / relativa)

    def prueba_reporte_fuera_de_ejecuciones(self, auditor, ejecucion_valida,
                                            tmp_path):
        """Una copia del reporte fuera de ejecuciones/ se rechaza."""
        copia = tmp_path / 'otra' / 'x' / 'reporte.json'
        copia.parent.mkdir(parents=True)
        copia.write_bytes(ejecucion_valida.read_bytes())
        with pytest.raises(ValueError):
            auditor.consultar('auditor', copia)

    def prueba_permiso_antes_que_lectura(self, auditor, tmp_path):
        """Con un reporte inexistente, el analista recibe PermissionError."""
        with pytest.raises(PermissionError):
            auditor.consultar('analista', tmp_path / 'ausente.json')


class PruebaFallosControlados:
    """Fallos del entorno quedan en el reporte sin interrumpir la auditoría."""

    def prueba_sin_clave(self, entorno, auditor, monkeypatch):
        """Sin DATAOPS_KEY: INTEGRIDAD pasa, EJECUCION FALLIDO por ValueError."""
        monkeypatch.delenv('DATAOPS_KEY')
        ruta = auditor.auditar('operador', entorno.entrada,
                               entorno.referencia)
        reporte = leer_reporte(ruta)
        assert estados(reporte) == {
            'INTEGRIDAD': 'SATISFACTORIO',
            'EJECUCION': 'FALLIDO',
            'CIFRADO': 'NO_EVALUADO',
            'MINIMIZACION': 'NO_EVALUADO',
            'ACCESO_DENEGADO': 'NO_EVALUADO',
            'TRAZABILIDAD': 'NO_EVALUADO',
        }
        assert reporte['hash_entrada'] == (
            entorno.referencia.read_text().strip())
        assert not (ruta.parent / 'salidas').exists()

    def prueba_entrada_ausente(self, entorno, auditor):
        """Una entrada inexistente deja EJECUCION FALLIDO por FileNotFoundError."""
        ruta = auditor.auditar('operador', entorno.base / 'no_existe.csv',
                               entorno.referencia)
        controles = {c['control']: c for c in leer_reporte(ruta)['controles']}
        assert controles['EJECUCION']['estado'] == 'FALLIDO'
        assert controles['EJECUCION']['evidencia'] == 'FileNotFoundError'
        assert controles['INTEGRIDAD']['estado'] == 'NO_EVALUADO'

    def prueba_comprobacion_pendiente(self, entorno):
        """Una comprobación sin implementar queda NO_EVALUADO, no aprobada."""
        class Pendiente:
            def verificar(self, *_args):
                raise NotImplementedError('TODO 6: comprobar_minimizacion')
        ruta = AuditorNova(entorno.ejecuciones,
                           minimizacion=Pendiente()).auditar(
            'operador', entorno.entrada, entorno.referencia)
        assert estados(leer_reporte(ruta))['MINIMIZACION'] == 'NO_EVALUADO'

    def prueba_comprobacion_que_falla(self, entorno):
        """Una comprobación que lanza un error queda FALLIDO."""
        class Rota:
            def verificar(self, *_args):
                raise OSError('lectura fallida')
        ruta = AuditorNova(entorno.ejecuciones, trazabilidad=Rota()).auditar(
            'operador', entorno.entrada, entorno.referencia)
        controles = {c['control']: c for c in leer_reporte(ruta)['controles']}
        assert controles['TRAZABILIDAD']['estado'] == 'FALLIDO'
        assert controles['TRAZABILIDAD']['accion'] == 'Revisar OSError'

    def prueba_resultado_no_booleano(self):
        """Solo True cuenta como satisfactorio; un valor verdadero no basta."""
        reporte = ReporteAuditoria()
        reporte.revisar('CIFRADO', lambda: 'si', 'evidencia')
        assert reporte.estado('CIFRADO') == 'FALLIDO'


class PruebaNoSobrescritura:
    """Cada auditoría usa una carpeta nueva y conserva las anteriores."""

    def prueba_dos_ejecuciones_independientes(self, entorno, auditor,
                                              ejecucion_valida):
        """Una segunda auditoría no toca los bytes de la primera."""
        carpeta = ejecucion_valida.parent
        antes = {p: p.read_bytes() for p in carpeta.rglob('*') if p.is_file()}
        segunda = auditor.auditar('operador', entorno.entrada,
                                  entorno.referencia)
        assert segunda.parent != carpeta
        assert {p: p.read_bytes() for p in carpeta.rglob('*')
                if p.is_file()} == antes
        assert len(list(entorno.ejecuciones.iterdir())) == 2

    def prueba_run_id_repetido(self, entorno, auditor, monkeypatch):
        """Si el run_id ya existe se lanza FileExistsError sin escribir."""
        class IdFijo:
            hex = 'a' * 32
        monkeypatch.setattr(lab2.uuid, 'uuid4', lambda: IdFijo())
        primera = auditor.auditar('operador', entorno.entrada,
                                  entorno.referencia)
        antes = primera.read_bytes()
        with pytest.raises(FileExistsError):
            auditor.auditar('operador', entorno.entrada, entorno.referencia)
        assert primera.read_bytes() == antes
