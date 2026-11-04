# Instalar ArquiModel

La carpeta de destino debe llamarse `arquimodel` para invocar la habilidad como `$arquimodel`. Necesitas Git y Codex. El repositorio contiene el código de la habilidad; cada motor de diagramas se instala por separado.

## Windows (PowerShell)

```powershell
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex\skills' }
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
git clone https://github.com/JanGP17/Skill-generador-de-diagramas.git (Join-Path $skillsDir 'arquimodel')
```

## macOS y Linux (Bash)

```bash
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skills_dir"
git clone https://github.com/JanGP17/Skill-generador-de-diagramas.git "$skills_dir/arquimodel"
```

Abre una conversación nueva en Codex para que detecte la habilidad. Para instalar exactamente la primera versión publicada, añade `--branch v1.0.0 --depth 1` al comando `git clone` antes de la URL.

## Actualizar

Ejecuta `git pull --ff-only` dentro de la carpeta `arquimodel`. Por ejemplo, en PowerShell:

```powershell
git -C (Join-Path $skillsDir 'arquimodel') pull --ff-only
```

## Herramientas para generar diagramas

El análisis, el posicionamiento y los controles de calidad usan Python 3.10 o posterior. PlantUML requiere Java y un archivo `plantuml.jar`; indica su ruta con la variable `PLANTUML_JAR` o con `--plantuml-jar`. Si no configuras ninguna de las dos, el renderizador busca `~/tools/plantuml/plantuml.jar`. Mermaid requiere el comando `mmdc` en `PATH`. Los diagramas Visio requieren Windows, PowerShell y Microsoft Visio de escritorio. La incrustación opcional de Visio en Word usa OfficeCLI.

Puedes comprobar la instalación con:

```powershell
python (Join-Path $skillsDir 'arquimodel\scripts\diagram_quality.py') --help
```
