# ArquiModel

Habilidad para modelar sistemas a partir de código y fuentes verificables. Genera diagramas con Visio, PlantUML y Mermaid, y conserva la trazabilidad de sus elementos.

## Instalar en Codex

Necesitas **Git** y **Codex**. Ejecuta el bloque de tu sistema operativo; la carpeta de destino debe llamarse `arquimodel`.

**Windows — PowerShell**

```powershell
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex\skills' }
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
git clone https://github.com/JanGP17/Skill-generador-de-diagramas.git (Join-Path $skillsDir 'arquimodel')
```

**macOS y Linux — Bash**

```bash
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skills_dir"
git clone https://github.com/JanGP17/Skill-generador-de-diagramas.git "$skills_dir/arquimodel"
```

Abre una conversación nueva en Codex y escribe `$arquimodel`. Si la carpeta ya existe, sigue la sección [Actualizar](INSTALL.md#actualizar) en lugar de repetir `git clone`.

## Requisitos a primera vista

| Para | Necesitas | Comprobación |
|---|---|---|
| Análisis, trazabilidad y controles | Python 3.10 o posterior | `python --version` |
| UML con PlantUML (`.puml` → `.svg`) | Java y `plantuml.jar` | `java -version` |
| Flujo, ER, secuencia narrativa y Gantt con Mermaid (`.mmd` → `.svg`) | Node.js, npm y Mermaid CLI en `PATH` | `mmdc --version` |
| Diagramas editables Visio (`.json` → `.vsdx`) | Windows, PowerShell y Microsoft Visio de escritorio | `New-Object -ComObject Visio.InvisibleApp` |
| Objeto Visio editable dentro de Word | OfficeCLI y un DOCX de destino; Word y Visio para edición interactiva | Solo para esa función opcional |

PlantUML puede requerir Graphviz para algunos tipos de UML, especialmente fuera de Windows. La instalación de la habilidad no instala los motores. Puedes usar las funciones cuyos requisitos tengas disponibles. Los scripts principales de Python usan la biblioteca estándar; **PyYAML no es necesario** para los flujos incluidos. Consulta [la instalación detallada](INSTALL.md) para configurar cada motor y comprobarlo.

## Qué hace

ArquiModel identifica candidatos en el código sin ejecutarlo, pide confirmar cada elemento mediante fuentes y distingue lo implementado de lo documentado o propuesto. Crea modelos UML, entidad-relación, flujos y arquitectura funcional. Conserva los archivos fuente y comprueba sintaxis, integridad, trazabilidad y legibilidad antes de dar una figura por revisada.

El selector `scripts/select_diagram_engine.py` elige PlantUML para notación UML y Mermaid para flujo, ER, secuencia narrativa y Gantt. Si se solicita un VSDX de un tipo compatible, dirige a uno de los generadores Visio existentes. Los diagramas densos pueden dividirse en vistas con un inventario de continuidad.

## Archivos del repositorio

- [SKILL.md](SKILL.md): instrucciones que carga Codex.
- [scripts/](scripts/): análisis, generación, posicionamiento y control de calidad.
- [references/](references/): criterios de modelado y uso de cada motor.
- [tests/](tests/): pruebas de selección de motor, trazabilidad y colocación de rótulos.
- [INSTALL.md](INSTALL.md): instalación, actualización y diagnóstico por comandos.

La habilidad está orientada a proyectos de Ingeniería Informática de la Universidad Nacional de Trujillo. Sus umbrales visuales son criterios técnicos configurables. Consulta la guía vigente de tu escuela para los requisitos institucionales.

## Autoría y licencia

Proyecto publicado por [JanGP17](AUTHORS.md) bajo [licencia MIT](LICENSE).
