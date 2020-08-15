import src.firebase.config as config

_database = config.firebase.database()


def insertar_registro(registro):
    """
    Inserta un nuevo registro en Firebase Real Time Database

    :param registro: El objeto de la persona capturada que se va a registrar en la base de datos
    :type registro: dict
    """
    _database.child('registros').push(registro)
