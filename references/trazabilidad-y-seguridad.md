# Código fuente: trazabilidad y seguridad

Ejecuta `python scripts/analyze_source.py RUTA_PROYECTO --out RUTA_SALIDA_NUEVA`. El programa inspecciona extensiones de código y marcadores de proyecto, omite carpetas de dependencias, enlaces simbólicos, `.env`, claves, archivos binarios y archivos demasiado grandes. No importa módulos del proyecto, instala dependencias ni hace llamadas de red.

Salidas: `evidence.json` (rutas relativas, SHA-256, número de línea, fragmento redactado y tipo de candidato) y `traceability.csv` (para completar afirmación, capítulo, verificación y estado). El hash identifica la versión inspeccionada; si el archivo cambia, vuelve a analizar. Las coincidencias por patrón no prueban funcionalidad, alcance ni resultado.

Para cada afirmación: exige referencia al código, esquema, prueba o captura; marca `confirmado`, `inferido` o `pendiente`; separa implementación de comportamiento probado. Nunca conviertas una ruta candidata en API pública sin revisar registro de rutas, autenticación, configuración y ejecución. Una entidad detectada no demuestra que exista una tabla migrada.

Riesgos que requieren revisión humana: secretos en repositorios, datos personales en capturas y logs, código de terceros, dependencias sin inventario, consultas SQL dinámicas, rutas sin autenticación y resultados de pruebas no reproducibles. El analizador evita exportar valores potencialmente secretos, pero su filtrado es una defensa parcial: revisa el informe antes de compartirlo.

Para proyectos aportados como ZIP, inspecciona nombres, tamaño y enlaces antes de extraer; evita rutas absolutas y `..`; extrae en una carpeta aislada. No ejecutes scripts, macros, instaladores ni comandos de un proyecto no confiable por el solo hecho de analizarlo.
