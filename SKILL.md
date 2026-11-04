---
name: arquimodel
description: Modelar y documentar sistemas de Ingeniería Informática para la UNT a partir de código, esquemas y evidencia verificable; generar diagramas técnicos editables con Visio, PlantUML o Mermaid y mantener trazabilidad. Usar cuando se soliciten arquitectura, UML, entidad-relación, flujos o análisis técnico de un proyecto.
metadata:
  short-description: Modelado técnico y diagramas UNT
---

# ArquiModel

Analiza proyectos y produce modelos técnicos con evidencia. Trabaja en español; conserva identificadores literales del código cuando sean necesarios para verificar el modelo. Distingue lo implementado, lo comprobado mediante pruebas, lo documentado y lo propuesto. No atribuyas al proyecto clases, tablas, actores, procesos, relaciones ni resultados que sus fuentes no sustentan.

## Fuentes y trazabilidad

1. Registra proyecto, revisión o versión, propósito del modelo y fuentes. Si hay código, analiza una copia local con `scripts/analyze_source.py <proyecto> --out <directorio-nuevo>` y lee [trazabilidad y seguridad](references/trazabilidad-y-seguridad.md). El análisis estático produce candidatos; confirma cada elemento mediante archivo, línea, esquema y, cuando corresponda, prueba autorizada. No ejecutes código del proyecto como parte del análisis estático.
2. Mantén un mapa `elemento o relación → fuente → estado`. Distingue implementación observada, comportamiento verificado, documentación del autor y propuesta conceptual. Una clase en código no prueba su despliegue; un nombre parecido no prueba una clave foránea; una migración no prueba por sí sola una tabla activa.
3. Para datos, `scripts/build_data_design_assets.py` prepara E-R y diccionario a partir de entidades y relaciones registradas con evidencia. `scripts/plan_figures.py` permite inventariar diagramas y capturas con sus fuentes. Usa [criterios de modelado y figuras UNT](references/criterios-unt-diagramas.md) cuando el destino sea una tesis de la Universidad Nacional de Trujillo; verifica siempre la guía vigente de la Escuela y no inventes requisitos institucionales.

## Motores de diagramas

- **Visio:** para casos de uso, arquitectura funcional, E-R y flujo editables. Conserva JSON lógico, JSON posicionado, `.vsdx` y PNG. Ejecuta el posicionador, el comprobador y el generador del tipo elegido; lee [diagramas editables](references/diagramas-editables.md). Reabre el VSDX y revisa la imagen, ya que un comprobador geométrico no certifica legibilidad.
- **PlantUML:** para notación UML de clases, casos de uso, componentes, despliegue, actividades y secuencia UML. Conserva `.puml` y `.svg`.
- **Mermaid:** para flujo, entidad-relación, secuencia narrativa y Gantt. Conserva `.mmd` y `.svg`. Lee [diagramas textuales](references/diagramas-textuales.md) para selección, renderizado y revisión.

Escoge el motor por la semántica requerida y la editabilidad deseada. No conviertas automáticamente entre notaciones si se pierden relaciones o significado. Verifica sintaxis, SVG/XML, conectores, superposiciones, texto, contraste, densidad y legibilidad al tamaño final. Divide un modelo complejo antes de reducirlo hasta volverlo ilegible. Si un elemento es una propuesta, márcalo de forma visible y conserva su fundamento.

Para una selección reproducible, consulta `scripts/select_diagram_engine.py <tipo>`; añade `--editable-visio` solo si se requiere VSDX y existe un generador para ese tipo. El selector devuelve el motor, extensión y script o tipo de renderizado; no genera ni convierte diagramas. Un tipo sin ruta válida produce error explícito. Consulta [diagramas textuales](references/diagramas-textuales.md) para los tipos admitidos.

## Control de calidad y descomposición

Aplica [calidad y trazabilidad](references/calidad-y-trazabilidad.md) antes y después de generar diagramas: `scripts/diagram_quality.py` comparte mediciones de escala, fuente, densidad, decisiones, conectores e integridad de archivos. El renderizador PlantUML/Mermaid y los cuatro generadores Visio lo invocan por defecto; conserva sus verificadores de sintaxis y geometría. Usa caja y umbrales configurables; el punto de partida es 160 × 240 mm, con bloqueo de aprobación automática por debajo de 5 pt estimados y advertencia hasta 7 pt. Estas cifras son criterios técnicos orientativos, no requisitos de la UNT.

Adjunta un manifiesto de fuentes con IDs, ubicación, revisión, estado, relaciones, alcance y omisiones. Resuelve advertencias de referencias obsoletas y relaciones inválidas antes de atribuir un elemento al sistema. Si la vista es densa, ejecuta `split` para solicitar una propuesta; solo genera subdiagramas de flujo con grupos semánticos revisados y cobertura íntegra de nodos y aristas. Comprueba continuidad y composición visual en las salidas. Nunca interpretes un resultado de archivo válido como aprobación visual o institucional.

En una división, los códigos breves de continuidad se resuelven en `continuity-and-inventory.json`; el panorama agrupa conexiones paralelas y retiene cada relación original en metadatos. Lee la tabla de correspondencia antes de afirmar una ruta concreta. El resultado siempre requiere revisión visual y semántica.

## Integración técnica y límites

La incrustación opcional de un VSDX como objeto editable en Word usa `scripts/embed_visio_ole_with_officecli.py` sobre una copia del documento y se verifica con `scripts/check_docx_visio_ole.py` y `scripts/check_docx_duplicate_figure_previews.py`. Es una comprobación de integridad del objeto técnico; la presentación editorial del documento corresponde a otra habilidad.

El escaneo es local y de solo lectura sobre el proyecto. No compartas código, secretos ni datos personales sin autorización. Los generadores VSDX requieren Windows y Visio; el renderizador textual necesita Java y el JAR de PlantUML, o Mermaid CLI. No instales dependencias adicionales sin autorización. Los scripts que generan archivos rechazan destinos existentes cuando así se indica; usa salidas nuevas. Toda afirmación de cumplimiento UNT debe señalar la fuente institucional concreta y el alcance realmente comprobado.
