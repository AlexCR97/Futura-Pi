import src.firebase.config as config
import pathlib

_storage = config.firebase.storage()


def subir_imagen(ruta_bucket, ruta_imagen):
    """
    Sube y almacena una imagen en Firebase Storage Bucket

    :param ruta_bucket: La ruta de Firebase Storage Bucket en donde se va almacenar la imagen
    :type ruta_bucket: str

    :param ruta_imagen: La ruta local en donde se encuentra la imagen que sera subida a Firebase Storage Bucket
    :type ruta_imagen: str
    """
    _storage.child(ruta_bucket).put(ruta_imagen)


def descargar_imagenes(ruta_bucket, ruta_imagenes):
    """
    Descarga todas las imagenes de una ruta de Firebase Storage Bucket

    :param ruta_bucket: La ruta de Firebase Storage Bucket de donde se descargaran las imagenes
    :type ruta_bucket: str

    :param ruta_imagenes: La ruta local en donde se van a almacenar las imagenes descargadas
    :type ruta_imagenes: str
    """

    print('ruta_bucket:', ruta_bucket)
    print('ruta_imagenes:', ruta_imagenes)
    print()

    # Crear la carpeta de descarga si no existe
    pathlib.Path(ruta_imagenes).mkdir(parents=True, exist_ok=True)

    for imagen in _storage.child(ruta_bucket).list_files():
        ruta_descarga = ruta_imagenes + '/' + imagen.name

        # Brincar si es un directorio. Por ejemplo, 'Rostros/Nombre/'
        if ruta_descarga[-1:] == '/':
            continue

        # Crear carpeta si no existe
        lista_ruta = ruta_descarga.split('/')
        del lista_ruta[-1]
        separador = '/'
        ruta_descarga_normalizada = separador.join(lista_ruta)

        print('image.name:  ', imagen.name)
        print('ruta_descarga1:', ruta_descarga)
        print('ruta_descarga2:', ruta_descarga_normalizada)
        print()

        pathlib.Path(ruta_descarga_normalizada).mkdir(parents=True, exist_ok=True)

        imagen.download_to_filename(ruta_descarga)
