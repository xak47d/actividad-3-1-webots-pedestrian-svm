---
title: "Actividad 3.1 - Detección de Peatones con SVM"
source: "https://experiencia21.tec.mx/courses/663304/assignments/22121926?module_item_id=41364580"
author:
published: 2026-05-24
created: 2026-05-22
description:
tags:
  - "clippings"
---
Fecha de entrega: dom 24 de may de 2026 23:59

Sin calificar, 10 puntos posibles

En progreso

SIGUIENTE: Presentar tarea

Se permiten intentos ilimitados

Disponible hasta 24 de may de 2026 23:59

## Objetivo

---

Identificar la Máquina de Soporte Vectorial como una herramienta importante para la detección de peatones en vehículos autónomos.

## Instrucciones

---

1. Si es necesario, estudia el código y el video que explica la operación de la Máquina de Soporte Vectorial (SVM) aplicada a la detección de vehículos, los cuales están disponibles como materiales de aprendizaje en este módulo.
2. Ubica en Internet y descarga un dataset adecuado para la detección de peatones con SVM.
3. Haz las modificaciones necesarias al código presentado para la detección de vehículos para que se pueda procesar la detección de peatones usando el dataset seleccionado en el punto anterior.
4. Usando comentarios en tu código, indica las modificaciones de código que tuviste que hacer sobre el código original para que pudiera realizarse la detección de peatones. Si es el caso, reporta como bibliografía otras fuentes de información que consultaste para llegar a la solución.
5. Exporta tu modelo ya entrenado para que sea utilizado en el mundo de Webots compartido por el profesor. Dicho mundo, contendrá peatones y barriles que se interpondrán en el recorrido del vehículo autónomo.
6. Usa como controlador del vehículo autónomo del mundo de esta actividad el mismo que desarrollaste en la solución de la actividad anterior, es decir, seguidor de línea con controlador PID y agrega el código indicado en los siguientes pasos.
7. Para apoyar con la detección de obstáculos, peatones y barriles, en el mundo, el vehículo debe hacer uso del LiDAR con el que cuenta en la parte frontal. Se trata de un LiDAR de la marca Sick ([https://www.cyberbotics.com/doc/guide/lidar-sensors?version=omichel:develop) Enlaces a un sitio externo.](https://www.cyberbotics.com/doc/guide/lidar-sensors?version=omichel:develop\)). Este sensor deberá ser habilitado en el controlador del vehículo y leer un ángulo de 20 ó 30 grados (el valor por omisión del sensor es de 180 grados). La detección de obstáculos se debe limitar a 20 metros. El código C a continuación puede ser de ayuda para desarrollar el código en Python (este extracto de código fue tomado del controlador del vehículo del mundo city.wbt de los mundos muestra).
8. ![image.png](https://experiencia21.tec.mx/courses/663304/files/276838911/preview)
9. Además, de habilitar al seguidor la línea, la imagen de la cámara deberá ser usada para detectar peatones con el modelo de SVM. La imagen de la cámara del mundo compartido por el profesor tiene una resolución de 256 por 128. Dado que la imagen de la cámara no se ajusta a las dimensiones de las imágenes de entrenamiento del SVM, se recomienda hacer uso de la técnica de Sliding Window Search y de una región de interés. El siguiente enlace puede servir de guía para implementar dicha técnica: [https://medium.com/@ricardo.zuccolo/self-driving-cars-opencv-and-svm-machine-learning-with-scikit-learn-for-vehicle-detection-on-the-bf88860e055a Enlaces a un sitio externo.](https://medium.com/@ricardo.zuccolo/self-driving-cars-opencv-and-svm-machine-learning-with-scikit-learn-for-vehicle-detection-on-the-bf88860e055a)
10. Dado que existen obstáculos de dos tipos, cuando el LiDAR detecte el obstáculo y este sea el barril, el vehículo deberá aplicar freno de emergencia (se pasa velocidad cero a la velocidad crucero del vehículo), encender luces intermitentes y esperar a que el barril desaparezca (el barril desaparecerá de manera automática). Cuando el obstáculo sea validado por el SVM como un peatón, se aplicará frenado de emergencia sin encender luces intermitentes. Asegúrate de mostrar en la simulación el estado de las luces. El siguiente enlace muestra cómo activar/desactivar las luces intermitentes: [https://cyberbotics.com/doc/automobile/driver-library?tab-language=python#wbu\_driver\_set\_hazard\_flashers Enlaces a un sitio externo.](https://cyberbotics.com/doc/automobile/driver-library?tab-language=python#wbu_driver_set_hazard_flashers)
11. El mundo compartido por el profesor incluye un robot Supervisor y su controlador que permiten controlar la posición de los barrilles en el mundo. Asegúrate de que el mundo pueda tener acceso a dicho controlador y, por favor, no modifiques el código del controlador.
12. Como ya ha sido comentado, el mundo compartido por el profesor incluye un número de peatones distribuidos por todo el mundo. Estos peatones son controlados por un mismo controlador, el cual ya viene instalado en Webots, por lo que no es necesario incluir ningún otro controlador. Cada peatón tiene una trayectoria y una velocidad definidas y, por favor, no deberían ser modificadas.
13. La simulación dará comienzo a partir de que se ejecute el controlador externo del vehículo autónomo. El controlador del robot Supervisor y el controlador de los peatones quedarán en pausa hasta que que el controlador externo inicie.
14. Crea un video con una duración menor a cinco minutos donde expliques (todas las personas del equipo deben participar en el video):
	1. Los resultados del entrenamiento del SVM en forma de matriz de confusión.
		2. La operación del LiDAR en el controlador y su colaboración con el SVM.
		3. La simulación en el mundo donde se pueda observar el recorrido del vehículo operando como seguidor de línea, la detección de peatones y de barriles y el frenado de emergencia.
15. Sube tu video a tu canal de YouTube y guarda el enlace.
16. A manera de reporte, crea un documento que incluya tu script con los comentarios y el enlace de tu video en YouTube. Tanto el código como los comentarios son importantes para el documento. No olvides incluir portada con los requerimientos indicados en la rúbrica.
17. Los elementos de código y simulación indicados en estas instrucciones forman parte de la rúbrica que se aplicará durante la evaluación de la actividad.

## Especificaciones de entrega

---

- **Modalidad:** En equipos.
- **Medio de realización/entrega:** A través del botón "Entregar Tarea" de esta actividad.
- **Formato:** DOC/DOCX o PDF.
- **Nombre del entregable:** Actividad\_3.1\_Detección\_de\_Peatones\_EquipoXX
- La evaluación de la actividad se podrá revisar en la sección de "Calificaciones" en Canvas.

**IMPORTANTE:**

- El uso de herramientas de inteligencia artificial deberá declararse de manera explícita; en ningún caso se deberá presentar como propio un producto generado total o parcialmente por dichas herramientas. Cuando se utilicen, deberá indicarse la herramienta y el modelo empleado en la entrega, así como la finalidad de su uso (generación de código / depuración / optimización).
- Ejemplo: OpenAI. (2026). *ChatGPT (basado en GPT-4)* \[Modelo de lenguaje grande\], utilizado para generación de código y depuración. [https://chat.openai.com/ Enlaces a un sitio externo.](https://nam04.safelinks.protection.outlook.com/?url=https%3A%2F%2Fchat.openai.com%2F&data=05%7C02%7Cdavidant%40tec.mx%7C827e2a68f8ac4a47cea608de9b4cd903%7Cc65a3ea60f7c400b89345a6dc1705645%7C0%7C0%7C639118951517906122%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=e6gWi3JtzOsbIiAYmErCc541L1a72mb48a8FdKWOc10%3D&reserved=0 "Original URL: https://chat.openai.com/. Click or tap if you trust this link.")
- La responsabilidad final sobre el contenido entregado recae en el autor. El estudiante deberá asegurar que las soluciones presentadas se ajusten estrictamente a lo solicitado, evitando la inclusión de código innecesario, excesivamente complejo o no requerido. El incumplimiento de este criterio podrá derivar en penalizaciones en la evaluación de la actividad.

## Recursos de apoyo

---

Revisa nuevamente los Jupyter Notebooks de este módulo y selecciona las porciones de código adecuadas para la solución de esta actividad.

Rúbrica: Actividad 3.1

| Criterios | Calificaciones | Puntos |
| --- | --- | --- |
| Portada |  | /10 pts |
| Código y comentarios |  | /60 pts |
| Video demostrativo |  | /30 pts |

Recuerde que esta entrega contará para todos en su grupo Project Groups.

Elegir un tipo de presentación

o