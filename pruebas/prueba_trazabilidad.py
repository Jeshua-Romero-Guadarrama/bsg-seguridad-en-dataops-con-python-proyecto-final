"""Pruebas de VerificadorTrazabilidad y comprobar_trazabilidad (TODO 7)."""
import json

import pytest

import lab2
from lab2 import VerificadorTrazabilidad

RUN_ID = 'run_prueba'
FECHA = '2026-10-29T21:30:00.123456+00:00'
TRIPLES = [
    ('operador', 'ejecutar', 'PERMITIDO'),
    ('operador', 'pipeline', 'COMPLETADO'),
    ('analista', 'ejecutar', 'DENEGADO'),
]


def traza():
    """Devuelve los tres eventos de una ejecución válida."""
    return [
        {'run_id': RUN_ID, 'fecha_utc': FECHA, 'rol': rol,
         'operacion': operacion, 'resultado': resultado}
        for rol, operacion, resultado in TRIPLES
    ]


def escribir(ruta, registros):
    """Escribe los registros como JSONL en UTF-8."""
    ruta.write_text(''.join(json.dumps(r) + '\n' for r in registros),
                    encoding='utf-8')
    return ruta


def alterar(campo, valor, indice=0):
    """Devuelve una traza válida con un campo de un evento cambiado."""
    registros = traza()
    registros[indice][campo] = valor
    return registros


def sin_campo(campo, indice=0):
    """Devuelve una traza válida a la que le falta un campo."""
    registros = traza()
    del registros[indice][campo]
    return registros


# Las ocho variantes de comprobar_lab2.py y otras más.
VARIANTES = {
    'falta_evento_denegado': traza()[:-1],
    'falta_evento_completado': [traza()[0], traza()[2]],
    'run_id_distinto': alterar('run_id', 'otra_ejecucion'),
    'run_id_distinto_ultimo': alterar('run_id', 'otra_ejecucion', 2),
    'campo_extra_correo': alterar('correo', 'cliente@example.com'),
    'campo_extra_token': alterar('token', 'gAAAA'),
    'fecha_sin_zona': alterar('fecha_utc', '2026-10-26T10:00:00'),
    'fecha_otra_zona': alterar('fecha_utc', '2026-10-26T10:00:00+01:00'),
    'fecha_zona_negativa': alterar('fecha_utc', '2026-10-26T10:00:00-06:00'),
    'fecha_no_iso': alterar('fecha_utc', '29/10/2026 21:30'),
    'fecha_vacia': alterar('fecha_utc', ''),
    'rol_en_blanco': alterar('rol', '   '),
    'operacion_vacia': alterar('operacion', ''),
    'resultado_nulo': alterar('resultado', None),
    'resultado_numerico': alterar('resultado', 1),
    'run_id_lista': alterar('run_id', [RUN_ID]),
    'falta_resultado': sin_campo('resultado'),
    'falta_fecha': sin_campo('fecha_utc'),
    'resultado_en_minusculas': alterar('resultado', 'denegado', 2),
    'rol_cambiado': alterar('rol', 'auditor', 0),
}
CONTENIDOS = {
    'no_es_json': 'no_es_json\n',
    'vacio': '',
    'lista': '[]\n',
    'nulo': 'null\n',
    'numero': '42\n',
    'texto_json': '"evento"\n',
    'solo_saltos': '\n\n',
}


class PruebaTrazabilidadValida:
    """Una traza completa y correcta devuelve exactamente True."""

    def prueba_traza_valida(self, tmp_path):
        """Los tres eventos requeridos con el mismo run_id dan True."""
        ruta = escribir(tmp_path / 'eventos.jsonl', traza())
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True

    def prueba_orden_no_exigido(self, tmp_path):
        """El orden de los eventos no es un requisito."""
        ruta = escribir(tmp_path / 'eventos.jsonl', list(reversed(traza())))
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True

    def prueba_eventos_adicionales_validos(self, tmp_path):
        """Un evento extra bien formado no invalida la traza."""
        extra = dict(traza()[0], operacion='recuperar')
        ruta = escribir(tmp_path / 'eventos.jsonl', traza() + [extra])
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True

    def prueba_sufijo_z(self, tmp_path):
        """El sufijo Z también expresa UTC."""
        registros = [dict(r, fecha_utc='2026-10-29T21:30:00Z')
                     for r in traza()]
        ruta = escribir(tmp_path / 'eventos.jsonl', registros)
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True

    def prueba_traza_del_registrador(self, tmp_path):
        """Lo que escribe registrar_evento pasa la verificación."""
        ruta = tmp_path / 'eventos.jsonl'
        for rol, operacion, resultado in TRIPLES:
            lab2.registrar_evento(ruta, RUN_ID, rol, operacion, resultado)
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True

    def prueba_separador_unicode_en_un_valor(self, tmp_path):
        """U+2028 dentro de un valor no parte el evento en dos líneas."""
        ruta = tmp_path / 'eventos.jsonl'
        for rol, operacion, resultado in TRIPLES:
            lab2.registrar_evento(ruta, RUN_ID, rol, operacion, resultado)
        lab2.registrar_evento(ruta, RUN_ID, 'operador\u2028externo',
                              'consultar', 'PERMITIDO')
        assert '\u2028' in ruta.read_text(encoding='utf-8')
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True

    def prueba_no_modifica_el_registro(self, tmp_path):
        """La verificación solo lee: el archivo queda idéntico."""
        ruta = escribir(tmp_path / 'eventos.jsonl', traza())
        antes = ruta.read_bytes()
        VerificadorTrazabilidad().verificar(ruta, RUN_ID)
        VerificadorTrazabilidad().verificar(ruta, 'otro')
        assert ruta.read_bytes() == antes

    def prueba_no_llama_al_registrador(self, tmp_path, monkeypatch):
        """comprobar_trazabilidad no usa registrar_evento."""
        def prohibido(*_args, **_kwargs):
            raise AssertionError('registrar_evento no debe llamarse')
        monkeypatch.setattr(lab2, 'registrar_evento', prohibido)
        monkeypatch.setattr(lab2.RegistradorEventos, 'registrar', prohibido)
        ruta = escribir(tmp_path / 'eventos.jsonl', traza())
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is True


class PruebaTrazabilidadInvalida:
    """Cualquier incumplimiento devuelve False sin excepción."""

    @pytest.mark.parametrize('registros', list(VARIANTES.values()),
                             ids=list(VARIANTES))
    def prueba_variante_invalida(self, tmp_path, registros):
        """Campos, valores, run_id, fechas o eventos inválidos dan False."""
        ruta = escribir(tmp_path / 'eventos.jsonl', registros)
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is False

    @pytest.mark.parametrize('contenido', list(CONTENIDOS.values()),
                             ids=list(CONTENIDOS))
    def prueba_contenido_invalido(self, tmp_path, contenido):
        """JSON inválido, vacío u objetos de otro tipo dan False."""
        ruta = tmp_path / 'eventos.jsonl'
        ruta.write_text(contenido, encoding='utf-8')
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is False

    def prueba_linea_en_blanco_intermedia(self, tmp_path):
        """Una línea vacía entre eventos rompe el formato JSONL."""
        ruta = tmp_path / 'eventos.jsonl'
        lineas = [json.dumps(r) for r in traza()]
        ruta.write_text(lineas[0] + '\n\n' + '\n'.join(lineas[1:]) + '\n',
                        encoding='utf-8')
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is False

    def prueba_clave_repetida(self, tmp_path):
        """Un objeto con una clave duplicada se rechaza."""
        ruta = tmp_path / 'eventos.jsonl'
        lineas = [json.dumps(r) for r in traza()]
        lineas[0] = lineas[0][:-1] + ', "rol": "operador"}'
        ruta.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is False

    def prueba_no_utf8(self, tmp_path):
        """Bytes que no son UTF-8 dan False."""
        ruta = tmp_path / 'eventos.jsonl'
        ruta.write_bytes(b'\xff\xfe\xfa')
        assert lab2.comprobar_trazabilidad(ruta, RUN_ID) is False

    def prueba_archivo_ausente(self, tmp_path):
        """Un archivo inexistente da False."""
        assert lab2.comprobar_trazabilidad(tmp_path / 'ausente.jsonl',
                                           RUN_ID) is False

    def prueba_ruta_es_carpeta(self, tmp_path):
        """Una carpeta en lugar de un archivo da False."""
        assert lab2.comprobar_trazabilidad(tmp_path, RUN_ID) is False

    def prueba_run_id_esperado_distinto(self, tmp_path):
        """La misma traza no vale para otra ejecución."""
        ruta = escribir(tmp_path / 'eventos.jsonl', traza())
        assert lab2.comprobar_trazabilidad(ruta, 'otra_ejecucion') is False
