# Guía de Generación de Código Python Moderno para Backend (Gonzalo)

## Perfil del Desarrollador

* **Nombre:** Gonzalo
* **Rol:** Desarrollador Backend
* **Tecnologías Principales:**
    * Python 3.12+ (tipado fuerte, similar a Java)
    * FastAPI
    * PostgreSQL
    * Entorno de paquetes: UV (dependencias congeladas con `UV.lock`)
    * Contenedores: Docker

## Principios Generales para la Generación de Código

1.  **Modernidad y Relevancia:**
    * Priorizar siempre las últimas características y sintaxis de Python 3.12+.
    * Evitar patrones de código obsoletos o desaconsejados.
    * **Gestión de Tiempo:** Siempre usar la zona horaria local o especificarla explícitamente en lugar de `UTC` por defecto, a menos que se indique lo contrario. Evitar las suposiciones sobre `UTC`.
    * **Tipado Fuerte:** Utilizar *type hints* exhaustivamente en todas las funciones, variables y atributos de clase.

2.  **Calidad del Código:**
    * **Legibilidad:** El código debe ser claro, conciso y fácil de entender.
    * **Mantenibilidad:** Diseñar soluciones que sean fáciles de modificar, extender y depurar.
    * **Performance:** Considerar la eficiencia, especialmente en operaciones críticas de backend.
    * **Pruebas:** Aunque no se pida explícitamente, tener en mente la facilidad de testeo del código generado.

3.  **Estructura y Estilo:**
    * **Sin Condiciones Anidadas Excesivas:** Buscar alternativas como el patrón *Guard Clause* o refactorizar a funciones más pequeñas para evitar el anidamiento profundo.
    * **Funciones y Clases Pequeñas:** Diseñar funciones y clases con una única responsabilidad (SRP - Single Responsibility Principle).
    * **Convenciones PEP 8:** Adherirse estrictamente a las guías de estilo de PEP 8.
    * **Nomenclatura Clara:** Usar nombres descriptivos para variables, funciones y clases.

## Patrones de Diseño (Creacionales)

Los patrones de diseño son fundamentales para construir software robusto y escalable. Al generar código, se buscará aplicar los siguientes patrones cuando sea apropiado:

1.  **Builder:** * **Descripción:** Permite construir objetos complejos paso a paso. Útil cuando un objeto tiene muchas posibles configuraciones o cuando su construcción es un proceso complejo que debe separarse del objeto final.
    * **Uso en Backend:** Creación de consultas SQL dinámicas, objetos de configuración de servicios, o DTOs complejos.
    
2.  **Prototype:** * **Descripción:** Permite copiar objetos existentes sin que el código dependa de sus clases concretas. Útil cuando la creación de un objeto es costosa o cuando necesitas crear muchas instancias similares de un objeto.
    * **Uso en Backend:** Duplicar configuraciones de usuario, plantillas de respuesta, o estados de objetos para procesamiento paralelo.
    
3.  **Singleton:** * **Descripción:** Asegura que una clase tenga una única instancia y proporciona un punto de acceso global a dicha instancia. Útil para recursos compartidos como gestores de bases de datos, *loggers* o configuraciones.
    * **Uso en Backend:** Conexiones a bases de datos (ORM), clientes HTTP, *loggers* globales.
    
    > **Nota sobre Singleton:** Si bien es útil, su uso debe ser considerado cuidadosamente para no introducir un acoplamiento fuerte o dificultades en el testeo. Preferir la inyección de dependencias cuando sea posible para manejar instancias únicas de servicios.

## Consideraciones Adicionales para la IA

* **Modularidad:** Siempre que sea posible, estructurar el código en módulos y paquetes lógicos.
* **Manejo de Errores:** Incluir manejo de excepciones robusto y explícito.
* **Seguridad:** Tener en cuenta las mejores prácticas de seguridad (ej., evitar inyección SQL, manejo seguro de credenciales, validación de entradas).
* **Asincronismo:** Al usar FastAPI, aprovechar `async/await` para operaciones I/O intensivas (acceso a base de datos, llamadas a servicios externos).

## guia para uso de codigo Python.
    Al momento de generar codigo Python, 
    Recuerda que hacemos por lo general arquitectura hexagonal y tenemos 
    archivos que referencian a la capa de aplicacion en la carpeta DOC/HEXAGONAL_REFACTOR_PLAN.md

