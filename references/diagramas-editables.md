# Diagramas editables

Para figuras textuales en PlantUML/Mermaid y SVG, consulta [motores de diagramas textuales](diagramas-textuales.md). Esta ruta complementa los modelos y generadores Visio descritos aquí.

Se conservan cuatro pares `layout_*.py` / `check_*_layout.py` y sus generadores `generate_visio_*.ps1` adaptados. Las salidas `.vsdx` contienen formas de Visio editables; el PNG es solo vista previa. La generación requiere Windows con Microsoft Visio; Python 3.10+ basta para el posicionamiento y la comprobación geométrica.

Los cuatro generadores crean informes de calidad previos y posteriores al VSDX mediante `diagram_quality.py`, sin sustituir los comprobadores geométricos. Usa `-TraceManifest` y `-ProjectRoot` para verificar fuentes; `-QualityConfig`, `-QualityDisable` o `-SkipQuality` ajustan las comprobaciones. Los informes se guardan junto al VSDX. Revisa [calidad y trazabilidad](calidad-y-trazabilidad.md) para interpretar las estimaciones de legibilidad y las recomendaciones de división.

Para cada tipo, prepara un JSON lógico a partir de evidencia o de un diseño marcado como propuesto. Luego ejecuta, por ejemplo, para casos de uso:

```powershell
python scripts/layout_use_case_diagram.py modelo.json --out modelo.posicionado.json
python scripts/check_use_case_layout.py modelo.posicionado.json
pwsh -File scripts/generate_visio_use_case_diagram.ps1 -InputJson modelo.posicionado.json -OutputVsdx figura-01.vsdx -OutputPng figura-01.png
```

Sustituye `use_case` por `function_architecture`, `er` o `flowchart` en los tres nombres para los otros tipos. Revisa que el comprobador termine con código 0 y examina el PNG antes de usar el modelo. Para E-R y flujo, requiere cero superposiciones y cero cruces de conectores; divide figuras densas. Genera en rutas nuevas: los posicionadores y renderizadores no sobrescriben archivos existentes.

En arquitectura funcional, el posicionador adaptado presenta las funciones hijas con texto horizontal para mantener legibles los rótulos en español. Los modelos que necesiten conservar el diseño vertical anterior pueden fijar `"layout": {"leafOrientation": "vertical"}` en el JSON lógico. Comprueba siempre el PNG: la verificación geométrica no detecta texto visualmente incómodo.

Modelo mínimo de caso de uso:

```json
{
  "diagramType": "use_case",
  "title": "Casos de uso del sistema",
  "actors": [{"id": "usuario", "name": "Usuario", "useCases": ["Consultar reporte"]}]
}
```

Modelos mínimos adicionales:

```json
{
  "diagramType": "function_architecture",
  "systemName": "Sistema de ejemplo",
  "topGroups": [{"id": "cliente", "name": "Cliente", "children": ["Consultar reporte"]}],
  "backendName": "Servicios",
  "bottomGroups": [{"id": "admin", "name": "Administrador", "children": ["Gestionar usuarios"]}]
}
```

```json
{
  "diagramType": "single_entity",
  "title": "Entidad usuario",
  "entity": {"name": "Usuario", "attributes": [{"name": "id", "key": true}, "nombre"]}
}
```

```json
{
  "diagramType": "flowchart",
  "title": "Consulta de reporte",
  "layout": {"direction": "TB"},
  "nodes": [{"id": "inicio", "type": "start", "text": "Inicio"}, {"id": "consulta", "type": "process", "text": "Consultar reporte"}, {"id": "fin", "type": "end", "text": "Fin"}],
  "edges": [{"from": "inicio", "to": "consulta"}, {"from": "consulta", "to": "fin"}]
}
```

Registra para cada diagrama: identificador, propósito, evidencia de cada nodo y relación, archivo JSON, `.vsdx`, PNG y revisión visual. No inventes relaciones de base de datos a partir de nombres parecidos.

Si el usuario necesita edición dentro de Word, trabaja sobre una copia del DOCX y usa `embed_visio_ole_with_officecli.py` solo cuando OfficeCLI esté instalado. Después ejecuta `check_docx_visio_ole.py` y `check_docx_duplicate_figure_previews.py`; el paquete OLE dentro de `word/embeddings/` debe existir. Esta ruta es opcional y no fue probada aquí por faltar un documento de destino y OfficeCLI.
