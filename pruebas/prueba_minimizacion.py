"""Pruebas de VerificadorMinimizacion y comprobar_minimizacion (TODO 6)."""
import csv

import pytest

import lab2
from lab2 import VerificadorMinimizacion

RESUMEN_VALIDO = (
    'ciudad,total_ventas\n'
    'Merida,4000.00\nPuebla,2500.00\nVillahermosa,4250.00\n'
)
# Los seis contenidos inválidos que usa comprobar_lab2.py y otros más.
INVALIDOS = {
    'columna_personal': (
        'ciudad,total_ventas,correo\nMerida,4000.00,cliente@example.com\n'),
    'solo_encabezados': 'ciudad,total_ventas\n',
    'orden_invertido': 'total_ventas,ciudad\n4000.00,Merida\n',
    'archivo_vacio': '',
    'fila_incompleta': 'ciudad,total_ventas\nMerida\n',
    'columna_extra_en_fila': 'ciudad,total_ventas\nMerida,4000.00,extra\n',
    'encabezado_ajeno': 'ciudad,ventas\nMerida,4000.00\n',
    'encabezado_unico': 'ciudad\nMerida\n',
    'mayusculas': 'Ciudad,Total_Ventas\nMerida,4000.00\n',
    'valor_vacio': 'ciudad,total_ventas\nMerida,\n',
    'valor_en_blanco': 'ciudad,total_ventas\n   ,4000.00\n',
    'encabezado_duplicado': 'ciudad,total_ventas,ciudad\nMerida,1,Merida\n',
    'segunda_fila_incompleta': (
        'ciudad,total_ventas\nMerida,4000.00\nPuebla\n'),
}


class PruebaMinimizacionValida:
    """Un resumen con el esquema mínimo devuelve exactamente True."""

    def prueba_resumen_valido(self, tmp_path):
        """Tres ciudades con ciudad y total_ventas devuelven True."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_text(RESUMEN_VALIDO, encoding='utf-8')
        assert lab2.comprobar_minimizacion(ruta) is True

    def prueba_una_fila_basta(self, tmp_path):
        """Una sola fila completa es suficiente."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_text('ciudad,total_ventas\nMerida,4000.00\n',
                        encoding='utf-8')
        assert lab2.comprobar_minimizacion(ruta) is True

    def prueba_no_evalua_importes(self, tmp_path):
        """El esquema no juzga importes: ese control es otro."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_text('ciudad,total_ventas\nMerida,no_numerico\n',
                        encoding='utf-8')
        assert lab2.comprobar_minimizacion(ruta) is True

    def prueba_finales_de_linea_windows(self, tmp_path):
        """Un CSV con CRLF se lee igual que con LF."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_bytes(RESUMEN_VALIDO.replace('\n', '\r\n').encode('utf-8'))
        assert lab2.comprobar_minimizacion(ruta) is True

    def prueba_encabezados_configurables(self, tmp_path):
        """El verificador acepta otro esquema si se le indica."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_text('a,b\n1,2\n', encoding='utf-8')
        assert VerificadorMinimizacion(['a', 'b']).verificar(ruta) is True
        assert VerificadorMinimizacion().verificar(ruta) is False


class PruebaMinimizacionInvalida:
    """Todo lo que no cumple el esquema devuelve False sin excepción."""

    @pytest.mark.parametrize('contenido', list(INVALIDOS.values()),
                             ids=list(INVALIDOS))
    def prueba_contenido_invalido(self, tmp_path, contenido):
        """Encabezados distintos, vacío o filas incompletas dan False."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_text(contenido, encoding='utf-8')
        assert lab2.comprobar_minimizacion(ruta) is False

    def prueba_no_utf8(self, tmp_path):
        """Bytes que no son UTF-8 dan False."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_bytes(b'\xff\xfe\xfa')
        assert lab2.comprobar_minimizacion(ruta) is False

    def prueba_latin1(self, tmp_path):
        """Un CSV en Latin-1 con caracteres acentuados da False."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_bytes('ciudad,total_ventas\nMérida,1\n'.encode('latin-1'))
        assert lab2.comprobar_minimizacion(ruta) is False

    def prueba_archivo_ausente(self, tmp_path):
        """Un archivo inexistente da False."""
        assert lab2.comprobar_minimizacion(tmp_path / 'ausente.csv') is False

    def prueba_ruta_es_carpeta(self, tmp_path):
        """Una carpeta en lugar de un archivo da False."""
        assert lab2.comprobar_minimizacion(tmp_path) is False

    def prueba_comilla_sin_cerrar(self, tmp_path):
        """Una comilla sin cerrar deja la fila incompleta y da False."""
        ruta = tmp_path / 'resumen.csv'
        ruta.write_text('ciudad,total_ventas\n"Merida,4000.00\n',
                        encoding='utf-8')
        assert lab2.comprobar_minimizacion(ruta) is False

    def prueba_campo_mayor_que_el_limite(self, tmp_path):
        """Un campo mayor que field_size_limit lanza csv.Error y da False."""
        ruta = tmp_path / 'resumen.csv'
        largo = 'x' * (csv.field_size_limit() + 1)
        ruta.write_text(f'ciudad,total_ventas\n{largo},4000.00\n',
                        encoding='utf-8')
        assert lab2.comprobar_minimizacion(ruta) is False

    def prueba_detalle_protegido_rechazado(self, ejecucion_valida):
        """El detalle con datos cifrados no pasa como resumen mínimo."""
        detalle = ejecucion_valida.parent / 'salidas' / 'detalle_protegido.csv'
        assert lab2.comprobar_minimizacion(detalle) is False
