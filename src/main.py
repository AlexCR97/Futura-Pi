import src.config as config
import src.firebase.bucket as bucket
import src.opencv.reconocedor as reconocedor
import src.opencv.entrenador as entrenador


def main():
    print('Main')

    ruta_modelo = config.ruta_modelos + '\\modelo_7-22-2020_12-16-AM.xml'
    ruta_imagenes = config.ruta_img

    print(ruta_modelo)
    print(ruta_imagenes)

    print('Inicializando reconocedor...')
    reconocedor.inicializar(ruta_modelo, ruta_imagenes)
    print('Reconocedor inicializado!')

    reconocedor.iniciar()


def main2():
    # print('Subiendo imagen...')
    # bucket.subir_imagen('test/bicho', 'C:\\Users\\carp_\\OneDrive\\Imágenes\\Icons\\bug.png')
    # print('Imagen subida!')
    print('Descargando imagenes...')
    bucket.descargar_imagenes('test', 'D:/Faces')


def main4():
    #entrenador.generar_modelo(config.ruta_modelos, config.ruta_img_entrenamiento + '/Rostros 3')
    ultimo_modelo = entrenador.ultimo_modelo()
    ultimo_registro = reconocedor.ultimo_registro()
    reconocedor.inicializar(ultimo_modelo, ultimo_registro, config.ruta_img_entrenamiento + '/Rostros 3')
    reconocedor.iniciar()


if __name__ == '__main__':
    #main()
    #main2()
    main4()
