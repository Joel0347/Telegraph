# Repositorio para la entrega de proyectos de la asignatura Sistemas Distribuidos en el curso 2025

## Cada equipo debe:

1. Crear un issue en el presente repositorio que contenga el nombre completo de sus integrantes, grupo, tema asignado y link al repo que da solución a su problemática
2. Cumplir con los requisitos generales de los proyectos.
3. Cumplir con el cronograma de entrega de las evaluaciones.

## Requisitos generales para una entrega válida del proyecto

1. Trabajo individual demostrable mediante el uso extensivo del sistema de control de versiones GIT.
2. Cada solución final debe poseer mínimo un nivel de tolerancia a fallos de nivel 2.
3. Cada proyecto debe cumplir como objetivo de diseño la indiferencia de su solución frente a una solución centralizada.
4. Toda propuesta requiere el empleo de alguna forma de toma de decisiones distribuidas.
5. Cada equipo debe de presentar su solución sobre una infraestructura de red compuesta sustentada sobre una red virtualizada de swarm que se ejecuta sobre mínimo dos ordenadores.

## 1ra Entrega 

Para cumplir con la 1ra entrega de los proyectos, cada equipo debe presentar una solución centralizada de su tema asignado.

## 2da Entrega

Para cumplir con la 2da entrega de los proyectos, cada equipo debe presentar un informa con los distintos roles, arquitecturas, procesos y funcionalidades de su sistema distribuido. Dicho informe quedará adjunto a su proyecto en git.

### Temáticas a contener en el informe:

1. Arquitectura o el problema de como diseñar el sistema.

* Organización de su sistema distribuido
* Roles de su sistema
* Distribución de servicios en ambas redes de docker

2. Procesos o el problema de cuantos programas o servicios posee el sistema

* Tipos de procesos dentro del sistema.
* Organización o agrupación de los procesos en una instancia, o en varias según su arquitectura
* Tipo de patrón de diseño con respecto al desempeño, async, hilos, procesos o algun subconjunto de los mismos.

3. Comunicación o el problema de como enviar información mediante la red

* Tipo de comunicación, rpc, sockets, rest, objetos remotos, patrones de mensajes, etc
* Comunicación cliente - servidor y servidor - servidor
* Comunicación entre procesos.

4. Coordinación o el problema de poner todos los servicios de acuerdo

* Sincronización de acciones. ( de ser necesario )
* Acceso exclusivo a recursos. Condiciones de carrera
* Toma de decisiones distribuidas.

5. Nombrado y Localización o el problema de dónde se encuentra un recurso y como llegar al mismo

* Identificación de los datos y servicios
* Ubicación de los datos y servicios
* Localización de los datos y servicios

6. Consistencia y Replicación o el problema de solucionar los problemas que surgen a partir de tener varias copias de un mismo dato en el sistema.

* Distribución de los datos
* Replicación, cantidad de réplicas.
* Confiabilidad de las réplicas de los datos tras una actualización.

7. Tolerancia a fallas o el problema de, para que pasar tanto trabajo distribuyendo datos y servicios si al fallar una componente del sistema todo se viene abajo.

* Respuesta a errores
* Nivel de tolerancia a fallos esperado.
* Fallos parciales. Nodos caídos temporalmente. Nodos nuevos que se incorporan al sistema.

8. Seguridad o el problema de que tan vulnerable es su diseño

* seguridad con respecto a la comunicación
* seguridad con respecto al diseño
* Autorización y autenticación.

## Consideraciones Finales

Cualquier enriquecimiento de los proyectos se tomará como positivo para la nota del equipo correspondiente. En particular proponemos dos requisitos adicionales para poder tener derecho a la revalorización y al extraordinario:

1. Interfaz gráfica con plena capacidad de funcionalidades
2. Seguridad de la comunicación y los procesos involucrados en su sistema

Siendo requisito para la revalorización tener al menos una de las dos funcionalidades anteriormente mencionadas y para el mundial ambas implementadas en el proyecto.

Toda modificación de los requerimientos del proyecto debe ser consultada con el claustro. En caso de que el claustro no de respuesta, asuman siempre la variante mas compleja de la interrogante.

Quedan vetados todos los sistemas que faciliten una comunicación distribuida que no se enseñen en clase, bibliotecas, softwares, etc.

Todo proyecto que emplee una solución basada en DHT obtiene por defecto una evaluación de 3 puntos, siempre que cumpla con todos los demás requisitos de entrega y funcionamiento.

Como refleja el reglamento docente, la asistencia influye sobre el derecho a presentación a examen. Para tener derecho a la primera presentación el equipo debe de haber aprobado 2 de las 3 evaluaciones principales del curso.
