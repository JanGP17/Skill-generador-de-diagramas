# Instalar y comprobar ArquiModel

El [README](README.md#instalar-en-codex) muestra los comandos de instalación al abrir el repositorio. Esta guía reúne los requisitos y las comprobaciones de cada función.

## 1. Instalar la habilidad

Necesitas Git y Codex. La carpeta instalada debe llamarse `arquimodel` para invocarla como `$arquimodel`.

### Windows (PowerShell)

```powershell
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex\skills' }
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
git clone https://github.com/JanGP17/Skill-generador-de-diagramas.git (Join-Path $skillsDir 'arquimodel')
```

### macOS y Linux (Bash)

```bash
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skills_dir"
git clone https://github.com/JanGP17/Skill-generador-de-diagramas.git "$skills_dir/arquimodel"
```

Abre una conversación nueva en Codex y escribe `$arquimodel`. Para instalar la versión `v1.1.0` en vez de la rama actual, añade `--branch v1.1.0 --depth 1` después de `git clone`. Una instalación fijada a un tag queda en estado detached; para recibir actualizaciones, instala la rama principal o cambia a `main` antes de actualizar.

## 2. Requisito común: Python

El análisis de código, el posicionamiento y los controles usan Python **3.10 o posterior**. Comprueba `python --version` o, en Windows, `py -3 --version`. Los scripts incluidos usan la biblioteca estándar de Python; no necesitas instalar PyYAML para estas funciones.

Comprueba la habilidad desde su carpeta:

```powershell
python scripts/select_diagram_engine.py uml-class
python scripts/diagram_quality.py --help
python -m unittest discover -s tests -v
```

## 3. PlantUML: diagramas UML

Instala Java y descarga `plantuml.jar` desde la [página oficial de PlantUML](https://plantuml.com/download). El renderizador busca el JAR en `PLANTUML_JAR` o, si la variable no está definida, en `~/tools/plantuml/plantuml.jar`. También puedes pasar `--plantuml-jar` al renderizador.

**PowerShell, para la sesión actual:**

```powershell
$env:PLANTUML_JAR = 'C:\ruta\a\plantuml.jar'
java -version
java -jar $env:PLANTUML_JAR -version
```

**Bash, para la sesión actual:**

```bash
export PLANTUML_JAR="$HOME/ruta/a/plantuml.jar"
java -version
java -jar "$PLANTUML_JAR" -version
```

Ejemplo de generación: `python scripts/render_text_diagram.py clases.puml --type uml-class --out clases.svg`.

Algunos tipos UML usan Graphviz. Compruébalo con `java -jar "$PLANTUML_JAR" -testdot` en Bash o `java -jar $env:PLANTUML_JAR -testdot` en PowerShell. Si PlantUML informa que falta `dot`, sigue la [guía oficial de Graphviz para PlantUML](https://plantuml.com/graphviz-dot). Las versiones recientes de PlantUML para Windows incluyen un ejecutable `dot` básico.

## 4. Mermaid: flujo, ER, secuencia narrativa y Gantt

Instala Node.js y npm según la [guía de npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm/). Después instala [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli):

```text
npm install -g @mermaid-js/mermaid-cli
mmdc --version
```

`mmdc` debe estar disponible en `PATH`. En Windows, el renderizador localiza `mmdc.cmd`; en macOS y Linux, `mmdc`. Ejemplo: `python scripts/render_text_diagram.py flujo.mmd --type flowchart --out flujo.svg`.

## 5. Visio: diagramas VSDX editables

Esta ruta requiere **Windows, PowerShell y Microsoft Visio de escritorio** instalado y activado. Comprueba la automatización COM con:

```powershell
$visio = New-Object -ComObject Visio.InvisibleApp
$visio.Quit()
```

Los generadores Visio aceptan modelos JSON posicionados y producen `.vsdx`; pueden exportar PNG para revisión. Están en `scripts/generate_visio_*_diagram.ps1`. El selector muestra los tipos disponibles:

```powershell
python scripts/select_diagram_engine.py flowchart --editable-visio
```

La generación de archivos y su apertura en Visio son comprobaciones técnicas. Revisa los rótulos, conectores y tamaño final antes de usar una figura en un documento.

## 6. Función opcional: Visio editable dentro de Word

La inserción de un VSDX como objeto OLE en un DOCX usa OfficeCLI y un documento de destino. Para editar el objeto de forma interactiva, necesitas un entorno con Word y Visio. Consulta `scripts/embed_visio_ole_with_officecli.py --help` y trabaja sobre una copia del documento. Esta función no interviene en la generación normal de diagramas.

## Actualizar

Si instalaste la rama principal y la carpeta no tiene cambios locales, ejecuta:

**PowerShell**

```powershell
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex\skills' }
git -C (Join-Path $skillsDir 'arquimodel') pull --ff-only
```

**Bash**

```bash
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
git -C "$skills_dir/arquimodel" pull --ff-only
```

Abre una conversación nueva en Codex para cargar la versión actualizada.
