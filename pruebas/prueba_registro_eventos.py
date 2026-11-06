"""Pruebas de RegistradorEventos y registrar_evento (TODO 5)."""
import json
from datetime import datetime, timedelta, timezone

import pytest

import lab2
from lab2 import CAMPOS_EVENTO, RegistradorEventos

FECHA_FIJA = datetime(2026, 10, 29, 21, 30, tzinfo=timezone.utc)
EVENTOS = [
    ('operador', 'ejecutar', 'PERMITIDO'),
    ('operador', 'pipeline', 'COMPLETADO'),
    ('analista', 'ejecutar', 'DENEGADO'),
]


def leer_eventos(ruta):
    """Devuelve la lista de objetos JSON del archivo, uno por línea."""
    return [json.loads(linea) for linea in
            ruta.read_text(encoding='utf-8').splitlines()]


class PruebaRegistroEventos:
    """Cada llamada anexa un objeto JSON completo con los campos exactos."""

    def prueba_anexa_tres_eventos(self, tmp_path):
        """Tres llamadas dejan tres líneas, en orden y con salto final."""
        ruta = tmp_path / 'eventos.jsonl'
        for rol, operacion, resultado in EVENTOS:
            lab2.registrar_evento(ruta, 'run_prueba', rol, operacion,
                                  resultado)
        contenido = ruta.read_text(encoding='utf-8')
        assert contenido.endswith('\n')
        eventos = leer_eventos(ruta)
        assert [(e['rol'], e['operacion'], e['resultado'])
                for e in eventos] == EVENTOS

    def prueba_no_sobrescribe_eventos_previos(self, tmp_path):
        """Un evento nuevo conserva byte a byte los anteriores."""
        ruta = tmp_path / 'eventos.jsonl'
        lab2.registrar_evento(ruta, 'run_prueba', *EVENTOS[0])
        antes = ruta.read_bytes()
        lab2.registrar_evento(ruta, 'run_prueba', *EVENTOS[1])
        assert ruta.read_bytes().startswith(antes)
        assert len(leer_eventos(ruta)) == 2

    def prueba_campos_exactos(self, tmp_path):
        """El evento tiene exactamente los cinco campos del contrato."""
        ruta = tmp_path / 'eventos.jsonl'
        lab2.registrar_evento(ruta, 'run_prueba', *EVENTOS[0])
        evento = leer_eventos(ruta)[0]
        assert list(evento) == list(CAMPOS_EVENTO)
        assert evento['run_id'] == 'run_prueba'
        assert all(isinstance(v, str) and v.strip() for v in evento.values())

    def prueba_fecha_utc_reciente(self, tmp_path):
        """fecha_utc es ISO, con desplazamiento cero y de este momento."""
        ruta = tmp_path / 'eventos.jsonl'
        lab2.registrar_evento(ruta, 'run_prueba', *EVENTOS[0])
        fecha = datetime.fromisoformat(leer_eventos(ruta)[0]['fecha_utc'])
        assert fecha.utcoffset() == timedelta(0)
        segundos = (datetime.now(timezone.utc) - fecha).total_seconds()
        assert abs(segundos) < 120

    def prueba_reloj_inyectado(self, tmp_path):
        """Con un reloj inyectado la fecha es exactamente la indicada."""
        ruta = tmp_path / 'eventos.jsonl'
        evento = RegistradorEventos(lambda: FECHA_FIJA).registrar(
            ruta, 'run_prueba', *EVENTOS[0])
        assert evento['fecha_utc'] == '2026-10-29T21:30:00+00:00'
        assert leer_eventos(ruta) == [evento]

    def prueba_utf8_sin_escapar(self, tmp_path):
        """El archivo es UTF-8 y conserva caracteres no ASCII legibles."""
        ruta = tmp_path / 'eventos.jsonl'
        lab2.registrar_evento(ruta, 'ejecución_ñ', *EVENTOS[0])
        assert 'ejecución_ñ' in ruta.read_bytes().decode('utf-8')
        assert leer_eventos(ruta)[0]['run_id'] == 'ejecución_ñ'

    def prueba_sin_datos_personales_ni_claves(self, tmp_path, monkeypatch):
        """Los eventos no copian correos, nombres ni la clave del entorno."""
        centinela = 'texto_centinela_del_entorno'
        monkeypatch.setenv('DATAOPS_KEY', centinela)
        ruta = tmp_path / 'eventos.jsonl'
        for rol, operacion, resultado in EVENTOS:
            lab2.registrar_evento(ruta, 'run_prueba', rol, operacion,
                                  resultado)
        texto = ruta.read_text(encoding='utf-8')
        assert '@' not in texto
        assert 'Cliente Prueba' not in texto
        assert centinela not in texto
        assert 'gAAAA' not in texto

    @pytest.mark.parametrize('campo', ['run_id', 'rol', 'operacion',
                                       'resultado'])
    @pytest.mark.parametrize('valor', ['', '   ', None])
    def prueba_rechaza_valores_vacios(self, tmp_path, campo, valor):
        """Un valor vacío o no textual se rechaza sin escribir nada."""
        argumentos = {'run_id': 'run_prueba', 'rol': 'operador',
                      'operacion': 'ejecutar', 'resultado': 'PERMITIDO'}
        argumentos[campo] = valor
        ruta = tmp_path / 'eventos.jsonl'
        with pytest.raises(ValueError, match=campo):
            RegistradorEventos().registrar(ruta, **argumentos)
        assert not ruta.exists()
