# Control técnico de calidad y trazabilidad

`scripts/diagram_quality.py` comparte las comprobaciones de los tres motores. Produce JSON de preflight y postflight, clasifica cada medición como `exact`, `estimated` o `unavailable` y nunca aprueba automáticamente una figura. La validez de SVG, PNG o VSDX tampoco prueba fidelidad semántica ni calidad visual.

## Uso

```powershell
python scripts/diagram_quality.py inspect --model figura.posicionado.json --vsdx figura.vsdx --png figura.png --trace trazabilidad.json --project-root C:\ruta\proyecto --out figura.calidad.json
python scripts/diagram_quality.py inspect --source figura.puml --svg figura.svg --out figura.calidad.json
python scripts/diagram_quality.py split --model flujo.json --out propuesta-nueva
python scripts/diagram_quality.py split --model flujo.json --groups grupos-revisados.json --out division-nueva
```

La caja orientativa inicial mide 160 × 240 mm. Una fuente estimada por debajo de 5 pt marca `blocked`; desde 5 y por debajo de 7 pt marca advertencia. A partir de 7 pt se siguen revisando densidad, proporción, conexiones y contenido. Son límites operativos configurables, no reglas de la UNT. El cálculo de escala supone ajuste uniforme del diagrama a la caja y puede diferir del tamaño real de inserción. Los tamaños SVG provienen de atributos declarados. Para Visio, si se aporta el VSDX, se leen las celdas de fuente de cada forma con texto y se usa la menor; el informe incluye los tamaños por ID de forma y cuenta las formas sin tamaño explícito. Antes de generar el VSDX, se usa `--font-pt` o el valor orientativo configurado. Las cifras de los archivos fuente textuales son aproximaciones sintácticas. Si falta una medición, el informe la indica.

Usa `--config ajustes.json` para sobrescribir solo las claves necesarias, por ejemplo:

```json
{
  "box_mm": {"width": 150, "height": 220},
  "font_pt": {"block_below": 5, "warn_below": 7, "visio_default": 9},
  "limits": {"nodes": 18, "edges": 24, "decisions": 6, "aspect_ratio": 3, "connector_diagonals": 12},
  "checks": {"readability": true, "density": true, "traceability": true, "decomposition": true}
}
```

`--disable readability,density` desactiva comprobaciones puntuales. `render_text_diagram.py` acepta `--quality-config`, `--quality-disable` y `--no-quality`; los generadores Visio aceptan `-QualityConfig`, `-QualityDisable` y `-SkipQuality`. Desactivar informes no equivale a aprobar una figura. Los generadores crean los informes junto a los archivos de salida y conservan sus verificadores geométricos originales.

## Manifiesto de evidencia

Registra `diagram_id`, `project_revision`, `scope`, `omissions`, `elements` y `relations`. Cada elemento y relación lleva `id` único, `name`, `type`, `status` (`implementado`, `documentado` o `propuesto`) y `sources`. Una fuente usa `path` relativo al proyecto, `start_line`, `end_line` y, si se dispone, `sha256`. Cada relación declara `from`, `to` y `label` (cadena vacía si no tiene rótulo), que deben corresponder a la arista del modelo. Para una propuesta sin fuente verificable, documenta `rationale` y conserva la advertencia. El inspector detecta IDs repetidos, extremos inexistentes, relaciones sin traza, líneas inválidas, archivos ausentes, cambio de hash y diferencia respecto a la revisión Git. El análisis estático solo aporta candidatos; revisa cada vínculo antes de afirmar implementación.

```json
{
  "diagram_id": "flujo-01",
  "project_revision": "HASH_DE_REVISION",
  "scope": "Vista parcial del flujo",
  "omissions": ["Detalle interno de persistencia"],
  "elements": [{"id": "validar", "name": "Validar acceso", "type": "process", "status": "implementado", "sources": [{"path": "apps/modulo/views.py", "start_line": 20, "end_line": 26, "sha256": "HASH_DE_ARCHIVO"}]}],
  "relations": []
}
```

## División

El comando `split` acepta un flujo estructurado con nodos y aristas. Sin grupos revisados crea solo `proposal.json`. Para generar vistas, aporta grupos semánticos con `id`, `title`, `basis` y `nodeIds`; cada nodo debe pertenecer exactamente a un grupo. El programa conserva cada arista original en su vista o registra dos referencias de continuidad cuando cruza grupos. Cada pareja de referencias comparte un código breve (`C01`, etc.); el informe `continuity-and-inventory.json` registra dirección, extremos originales, rótulo y grupo de destino. El panorama agrupa aristas paralelas por par de grupos dirigido para reducir saturación, pero cada arista original permanece identificada en `originalRelations`, `originalEdgeIds` y el inventario. El panorama es una abstracción; consulta el inventario para conocer la ruta exacta.

Los puertos breves se colocan al lado del flujo y los subdiagramas usan un espaciado más compacto. Ejecuta el posicionador y el comprobador geométrico antes de renderizar; revisa flechas, rótulos y correspondencias a tamaño de lectura. La generación queda `generated_for_review`, incluso cuando la estimación de fuente supera 7 pt. Para UML, ER y otros modelos se emite propuesta de revisión sin división automática, pues una partición geométrica podría perder multiplicidades, restricciones o significado.

La revisión visual al tamaño de lectura final sigue siendo obligatoria. Un diagrama denso puede necesitar reorganización o separación adicional aunque un informe no encuentre errores de archivo.
