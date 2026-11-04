# PlantUML y Mermaid para modelos técnicos

## Selección

| Necesidad | Motor predeterminado | Archivo fuente |
|---|---|---|
| Clases, casos de uso, componentes, despliegue o actividades con notación UML | PlantUML | `.puml` |
| Diagrama de flujo, entidad-relación, secuencia narrativa o Gantt | Mermaid | `.mmd` |
| Secuencia con semántica UML explícita | PlantUML | `.puml` |

La elección responde al tipo de notación solicitado; no conviertas automáticamente un modelo Visio o JSON a otra notación si la conversión pierde relaciones o semántica. La ruta existente [Visio editable](diagramas-editables.md) se mantiene para `.vsdx`, modelos JSON y PNG. Un `.svg` es vectorial y editable como gráfico, pero no equivale a un `.vsdx` ni a un objeto Visio OLE.

## Preparación y evidencia

Antes de escribir el código del diagrama, registra identificador de figura, propósito, fuente (ruta y versión de código, esquema, prueba, documento o declaración del autor), elementos/relaciones sustentados y estado `comprobado`, `inferido` o `propuesta conceptual`. Marca la propuesta de manera visible en el texto o nota de la figura. No inventes clases, métodos, multiplicidades, actores, procesos, módulos, participantes ni relaciones. Una clase detectada en código no prueba su despliegue; una tabla no implica una relación sin clave o esquema comprobado.

Redacta etiquetas técnicas en español, conservando identificadores literales del código cuando aporten trazabilidad. Usa pocos elementos por figura, jerarquía visual simple, contraste suficiente y tamaño legible al insertar en la página. En UML, aplica símbolos propios del tipo: visibilidad y multiplicidad solo si están verificadas; `include`/`extend`, dependencias y herencia solo con evidencia. Revisa la figura a tamaño de lectura, que no haya texto cortado o flechas ambiguas, y divídela si queda densa.

Si el destino es una tesis UNT, registra la fuente técnica del diagrama y consulta los [criterios de modelado UNT](criterios-unt-diagramas.md). La presentación editorial del manuscrito se revisa por separado. No conviertas recomendaciones visuales en requisitos institucionales no verificados.

## Renderizado local

`scripts/render_text_diagram.py` valida tipo y extensión, rechaza sobrescrituras y comprueba que el resultado sea SVG. Java y el JAR son necesarios para PlantUML; `mmdc` para Mermaid. El JAR se busca en `PLANTUML_JAR`, o por defecto en `~/tools/plantuml/plantuml.jar`; `--plantuml-jar` permite indicar otra ruta. No instales dependencias adicionales sin autorización.

El renderizador genera por defecto informes `.preflight.json` y `.quality.json`. Acepta `--png-out` para una vista PNG, `--trace` y `--project-root` para verificar evidencia, además de `--quality-config`, `--quality-disable` y `--no-quality`. Consulta [calidad y trazabilidad](calidad-y-trazabilidad.md) para los umbrales y sus límites.

```powershell
python scripts/render_text_diagram.py figuras\clases.puml --type uml-class --out figuras\clases.svg
python scripts/render_text_diagram.py figuras\proceso.mmd --type flowchart --out figuras\proceso.svg
```

Conserva ambos archivos junto a la ficha de evidencia y registra la herramienta/versión utilizada. Renderiza de nuevo tras cada cambio de fuente. Verifica la sintaxis mediante la ejecución del motor y revisa visualmente el SVG; la generación por sí sola no valida la semántica, la fidelidad al proyecto ni el cumplimiento de una guía UNT.
