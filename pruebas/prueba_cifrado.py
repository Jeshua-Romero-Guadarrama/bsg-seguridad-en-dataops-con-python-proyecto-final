"""Pruebas de VerificadorCifrado y comprobar_cifrado."""
import csv

import pytest
from cryptography.fernet import Fernet, InvalidToken

import lab2
from lab1 import CAMPOS, CifradorCampos, PipelineNova
from lab2 import VerificadorCifrado


def leer(ruta):
    """Devuelve las filas de un CSV como diccionarios."""
    with ruta.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def escribir(ruta, filas):
    """Escribe filas con las columnas del contrato."""
    with ruta.open('w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(filas)
    return ruta


@pytest.fixture
def detalle(entorno):
    """Genera un detalle protegido válido y devuelve su ruta."""
    destino = entorno.salidas / 'cifrado'
    return PipelineNova().ejecutar('operador', entorno.entrada,
                                   entorno.referencia, destino)['detalle']


class PruebaCifrado:
    """El detalle solo es válido si cada token recupera el original."""

    def prueba_detalle_valido(self, entorno, detalle):
        """El detalle generado por el pipeline devuelve True."""
        assert lab2.comprobar_cifrado(detalle, entorno.entrada) is True

    def prueba_cifrador_inyectado(self, entorno, detalle):
        """Con el cifrador de la clave correcta también devuelve True."""
        clave = entorno.clave.read_bytes().strip()
        cifrador = CifradorCampos(Fernet(clave))
        assert VerificadorCifrado(cifrador).verificar(
            detalle, entorno.entrada) is True

    def prueba_campo_en_claro(self, entorno, detalle):
        """Un correo sin cifrar devuelve False."""
        filas = leer(detalle)
        filas[3]['correo'] = leer(entorno.entrada)[3]['correo']
        escribir(detalle, filas)
        assert lab2.comprobar_cifrado(detalle, entorno.entrada) is False

    def prueba_token_de_otro_valor(self, entorno, detalle):
        """Un token válido de otro texto devuelve False."""
        filas = leer(detalle)
        cifrador = CifradorCampos.desde_entorno()
        filas[0]['nombre_cliente'] = cifrador.cifrar('Otro Cliente')
        escribir(detalle, filas)
        assert lab2.comprobar_cifrado(detalle, entorno.entrada) is False

    def prueba_filas_desordenadas(self, entorno, detalle):
        """Un pedido distinto en la misma posición devuelve False."""
        filas = leer(detalle)
        filas[0], filas[1] = filas[1], filas[0]
        escribir(detalle, filas)
        assert lab2.comprobar_cifrado(detalle, entorno.entrada) is False

    def prueba_fila_faltante(self, entorno, detalle):
        """Un detalle con menos filas que el original devuelve False."""
        escribir(detalle, leer(detalle)[:-1])
        assert lab2.comprobar_cifrado(detalle, entorno.entrada) is False

    def prueba_otra_clave(self, entorno, detalle, monkeypatch):
        """Con otra clave el token no se descifra: InvalidToken."""
        monkeypatch.setenv('DATAOPS_KEY', Fernet.generate_key().decode())
        with pytest.raises(InvalidToken):
            lab2.comprobar_cifrado(detalle, entorno.entrada)

    def prueba_sin_clave(self, entorno, detalle, monkeypatch):
        """Sin DATAOPS_KEY se lanza ValueError con el mensaje del material."""
        monkeypatch.delenv('DATAOPS_KEY')
        with pytest.raises(ValueError, match='Falta DATAOPS_KEY'):
            lab2.comprobar_cifrado(detalle, entorno.entrada)
