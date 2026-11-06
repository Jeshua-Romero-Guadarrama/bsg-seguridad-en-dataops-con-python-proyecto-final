"""Pruebas de PreparadorEntorno y de los componentes básicos del pipeline."""
import csv
import hashlib

import pytest
from cryptography.fernet import Fernet

from lab1 import CAMPOS, CalculadoraHuella, CifradorCampos
from preparar import PreparadorEntorno


class PruebaPreparadorEntorno:
    """El entorno se crea una sola vez y respeta el contrato."""

    def prueba_crea_los_tres_archivos(self, entorno):
        """Crea entrada, referencia y clave."""
        assert entorno.entrada.is_file()
        assert entorno.referencia.is_file()
        assert entorno.clave.is_file()

    def prueba_referencia_es_huella_del_original(self, entorno):
        """La referencia coincide con el SHA-256 del CSV generado."""
        esperado = hashlib.sha256(entorno.entrada.read_bytes()).hexdigest()
        assert entorno.referencia.read_text(encoding='ascii') == esperado

    def prueba_doce_filas_y_contrato(self, entorno):
        """El CSV tiene las columnas del contrato y 12 filas de datos."""
        with entorno.entrada.open(encoding='utf-8', newline='') as f:
            lector = csv.DictReader(f)
            filas = list(lector)
        assert lector.fieldnames == CAMPOS
        assert len(filas) == 12
        assert filas[0]['correo'] == 'cliente001@example.com'

    def prueba_no_reemplaza(self, entorno):
        """Una segunda preparación falla y conserva los archivos."""
        antes = [p.read_bytes() for p in
                 (entorno.entrada, entorno.referencia, entorno.clave)]
        with pytest.raises(FileExistsError, match='Entorno existente'):
            PreparadorEntorno(entorno.base).preparar()
        despues = [p.read_bytes() for p in
                   (entorno.entrada, entorno.referencia, entorno.clave)]
        assert despues == antes


class PruebaComponentes:
    """Huella y cifrado con contratos del tramo 1A."""

    def prueba_huella_detecta_un_cambio(self, entorno):
        """Cambiar un importe cambia la huella."""
        calculadora = CalculadoraHuella()
        alterada = entorno.alterar_entrada()
        assert calculadora.calcular(entorno.entrada) == (
            entorno.referencia.read_text().strip())
        assert calculadora.calcular(alterada) != (
            calculadora.calcular(entorno.entrada))

    def prueba_cifrado_recupera_el_valor(self):
        """Cifrar y descifrar devuelve el mismo texto; el token es ASCII."""
        cifrador = CifradorCampos(Fernet(Fernet.generate_key()))
        token = cifrador.cifrar('cliente001@example.com')
        assert isinstance(token, str) and token.startswith('gAAAA')
        assert cifrador.descifrar(token) == 'cliente001@example.com'

    def prueba_falta_clave(self, monkeypatch):
        """Sin DATAOPS_KEY se lanza ValueError con el mensaje del material."""
        monkeypatch.delenv('DATAOPS_KEY', raising=False)
        with pytest.raises(ValueError, match='Falta DATAOPS_KEY en el entorno'):
            CifradorCampos.desde_entorno()
