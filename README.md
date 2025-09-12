# Proyecto EduAI-SIMCE: Mejora del Desempeño Estudiantil en Matemáticas

## Descripción del Problema

### Definición

La capacidad del estudiantado chileno para rendir el SIMCE en Matemáticas se ve seriamente afectada. Gran parte de los estudiantes obtienen puntajes bajos debido a la existencia de tres brechas articuladas en su preparación:

1. **Currículo y Aula:** La enseñanza se enfoca en la cobertura de contenidos y la repetición de fórmulas, dejando de lado el desarrollo de la resolución de problemas contextualizados que el SIMCE exige.
   
2. **Formación Docente:** Muchos educadores no cuentan con herramientas didácticas adecuadas para diagnosticar errores conceptuales y ofrecer retroalimentación personalizada a sus estudiantes.
   
3. **Recursos Digitales Actuales:** Las plataformas existentes proporcionan únicamente bancos masivos de ejercicios con retroalimentación limitada a “correcto/incorrecto”, sin guiar al estudiante hacia una comprensión profunda ni adaptar el nivel de dificultad a sus necesidades.

Como resultado, los estudiantes practican sin un criterio claro, repiten errores y limitan sus estrategias de resolución.

### Justificación

Según las estadísticas recientes, más del 50% del estudiantado que rinde el SIMCE no alcanza el nivel adecuado en matemáticas. Este problema se agrava debido a la retroalimentación tardía y la falta de estandarización de los contenidos, lo que resalta la necesidad urgente de mejorar la calidad de la enseñanza y el aprendizaje en esta área.

## Tecnologías Usadas


![Flujo de trabajo](https://imgur.com/PGsLjWW.jpg)


Para abordar este desafío, se propone el desarrollo de un prototipo de plataforma web que incorpore:

- **Diagnóstico Preciso:** Para identificar las áreas que requieren atención específica.
- **Trayectorias de Aprendizaje Personalizadas:** Adaptando la enseñanza a las necesidades individuales de cada alumno.
- **Retroalimentación Cualitativa:** Ofreciendo orientaciones precisas para mejorar el razonamiento lógico.

![Librerias funcinamiento](https://imgur.com/QfgazC3.jpg)

### Diferenciación de Otras Plataformas

- **Bancos de Ejercicios:** Plataformas como DEMRE ofrecen retroalimentación cuantitativa ("correcto/incorrecto") pero carecen de una evaluación cualitativa que apoye el aprendizaje.
  
- **Plataformas como Evalua360 y Umaximo:** Aunque ofrecen reportes y estrategias innovadoras como juegos y evaluaciones con retroalimentación inmediata, la propuesta de este proyecto se distingue por el uso de **inteligencia artificial** para generar ejercicios personalizados. Además, se centra en la resolución de problemas, potenciando así el razonamiento lógico y, en consecuencia, mejorando los puntajes en el SIMCE.

## Capturas del sistema

## Guia de instalación proyecto

## Recursos
(hardware interno tabla y software externo modelo de nemotron y de donde lo obtengo y la clave)

## Estructura proyecto
```
tu-proyecto/
├── archivos_profesores   # Respaldo archivos docente
├───── loggin.png
├───── guia 1.pdf
├───── guia 2.pdf
├── testeo_fun             # Testeo de funciones sistema
├───── correo.py           # Envio de correos con smtp(pruebas basicas)
├───── funciones.md        # Lista de funcionalidades por rol en formato markdown
├───── prueballm.py        # Prueba de uso de cuestionarios
├── user_images            # Listado de imagenes de perfiles de usuario
├───── loggin.png
├───── loggin2.png
├───── loggin3.png
├───── loggin4.png
├── videos_tutoriales     # Archivos .mp4 dejados en el apartado de tutoriales 
├───── tutorial.mp4
├── index.py              # Archivo principal de la aplicación
├── requirements.txt      # Lista de dependencias
├── README.md             # Documentación del proyecto
├── users.db              # Base de datos sqlite(contiene el registro de usuarios)
└── .gitnore              # Archivo con las restricciones de elementos subidos al repositorio
```



## Conclusiones

Este proyecto busca transformar la manera en que los estudiantes chilenos se preparan para el SIMCE, proporcionando herramientas efectivas que aborden las brechas existentes en la enseñanza de las matemáticas. Con el uso de tecnologías avanzadas y un enfoque centrado en el aprendizaje profundo, el objetivo es mejorar el desempeño estudiantil de forma sostenible y significativa.



## Licencia

Este proyecto está bajo la [Licencia MIT](LICENSE).