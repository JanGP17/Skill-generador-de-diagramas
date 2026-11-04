# ArquiModel

ArquiModel ayuda a documentar sistemas informáticos a partir de código, esquemas y otras fuentes verificables. Genera diagramas editables con Visio y diagramas en SVG con PlantUML o Mermaid. Cada modelo puede conservar su fuente, sus relaciones y un informe de legibilidad.

La habilidad está orientada a proyectos de Ingeniería Informática de la Universidad Nacional de Trujillo. Sus umbrales visuales son criterios de trabajo configurables; las exigencias institucionales deben comprobarse en la guía vigente.

## Instalación

Se necesita Git para descargar la habilidad. Los comandos para Windows, macOS y Linux están en [INSTALL.md](INSTALL.md). Después de instalarla, abre una conversación nueva en Codex e invoca `$arquimodel`.

## Motores disponibles

| Motor | Uso principal | Requisitos locales |
|---|---|---|
| PlantUML | Clases, componentes y otros diagramas UML | Java y `plantuml.jar` |
| Mermaid | Flujos, entidad-relación, secuencia y Gantt | Mermaid CLI (`mmdc`) |
| Visio | Diagramas editables `.vsdx` | Windows y Microsoft Visio de escritorio |

Los scripts de análisis y control usan Python 3.10 o posterior. La generación con cada motor requiere sus herramientas locales; el repositorio no incluye Java, el JAR, Mermaid CLI ni Visio. La integración opcional de objetos Visio en Word requiere OfficeCLI.

## Archivos

- [SKILL.md](SKILL.md): instrucciones que carga Codex.
- [references/](references/): criterios técnicos, trazabilidad y uso de motores.
- [scripts/](scripts/): análisis, posicionamiento, generación y controles de calidad.
- [INSTALL.md](INSTALL.md): instalación y actualización por comandos.

## Autoría y licencia

Proyecto publicado por [JanGP17](AUTHORS.md). Distribuido bajo la [licencia MIT](LICENSE).
