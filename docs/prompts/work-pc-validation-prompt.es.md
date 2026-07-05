# Prompt: validacion controlada en PC de trabajo

Usa este prompt cuando quieras instalar y validar `ai-costguard` en un ordenador de trabajo con Cline, sin exponer secretos y sin tocar configuraciones reales hasta que el smoke aislado haya pasado.

````text
Quiero instalar y validar el repo `ai-costguard` en mi ordenador de trabajo de forma controlada y sin exponer secretos.

No ejecutes nada sobre mi HOME real hasta que yo lo confirme explicitamente.

Reglas de seguridad:
- No me pidas pegar secretos en el chat.
- No imprimas claves, tokens ni contenido sensible.
- No leas ni muestres `.env` si contiene secretos.
- No pases secretos como argumentos de comandos.
- No subas ni commitees `.env`.
- No modifiques repos de cliente.
- No toques ningun repo distinto a `ai-costguard` salvo que yo lo pida.
- No cambies configuracion real de Claude Code hasta que yo lo confirme.
- Primero valida todo con `COSTGUARD_HOME` y `COSTGUARD_CLAUDE_HOME` dentro del repo.

Primero lee:
- `README.md`
- `docs/RUNBOOK.md`
- `docs/SECURITY.md`
- `docs/TROUBLESHOOTING.md`
- `pyproject.toml`

Resume:
- que es Cost Guard
- como se instala
- como se configura Cline
- como se configura Claude Code
- como se desinstala
- que ficheros locales toca
- que componentes son obligatorios y cuales opcionales

Crea entorno local del repo:

```bash
python -m venv .venv
pip install -e .[dev]
pytest
```

Si `python` no esta en PATH en Windows, usa el lanzador disponible en el equipo, por ejemplo `py`, `uv`, o la ruta corporativa autorizada. No instales ni cambies Python global sin mi permiso.

Ejecuta smoke aislado, sin tocar mi HOME real.

Linux/macOS/Git Bash:

```bash
export COSTGUARD_HOME="$(pwd)/.tmp/costguard"
export COSTGUARD_CLAUDE_HOME="$(pwd)/.tmp/claude"
```

PowerShell:

```powershell
$env:COSTGUARD_HOME = "$(Get-Location)\.tmp\costguard"
$env:COSTGUARD_CLAUDE_HOME = "$(Get-Location)\.tmp\claude"
```

Luego ejecuta:

```bash
costguard --help
costguard setup --tool both --daily-budget 5 --monthly-budget 100 --budget-mode warn --non-interactive
costguard doctor
costguard cline-config
costguard status
costguard rules test "cat .env"
costguard rules test "git diff"
costguard rules test "find ."
costguard budget status
costguard usage today
costguard cache status
costguard headroom status
costguard uninstall --yes
pytest
```

En Windows, si `costguard` no esta en PATH, usa la ruta del entorno virtual:

```powershell
.\.venv\Scripts\costguard.exe --help
.\.venv\Scripts\costguard.exe doctor
```

En PowerShell no uses `&&`; ejecuta comandos separados o usa `;`.

Si todo esta OK, prepara setup real SOLO para Cline:

```bash
costguard setup --tool cline --daily-budget 5 --monthly-budget 100 --budget-mode warn --non-interactive
```

No configures Claude Code todavia.

Para secretos corporativos:
- indicame que fichero debo editar
- no imprimas el contenido sensible
- yo introducire manualmente la Base URL, API key y modelo corporativo en `.env`
- no pases secretos como flags ni los dejes en historial de comandos

Despues valida:

```bash
costguard doctor
costguard status
costguard cline-config
```

Muestrame que poner en Cline:

```text
Provider: OpenAI Compatible
Base URL: http://127.0.0.1:4040/v1
API Key: sk-costguard-local
Model ID: cg-standard
```

Para arrancar Cost Guard, explicame si `costguard start` bloqueara la terminal. Si bloquea, dime como dejarlo corriendo en otra terminal.

No configures Claude Code hasta que yo lo confirme.

Si confirmo Claude Code:
- comprueba si existe `~/.claude/settings.json`
- explica que se va a modificar
- confirma que se creara backup
- ejecuta `costguard setup --tool claude-code` solo cuando yo lo autorice
- valida despues con `costguard doctor`

Para uninstall:
- primero explicame que hara `costguard uninstall`
- no ejecutes `costguard uninstall --purge` salvo que yo lo pida
- valida que Claude Code vuelve a su configuracion previa si se toco

Al final resume:
- tests ejecutados
- smoke tests ejecutados
- si Cline quedo configurado
- si Claude Code quedo configurado
- como arrancar Cost Guard cada dia
- como ver consumo
- como cambiar presupuesto
- como editar reglas
- como desinstalar
- problemas encontrados
- cambios realizados en el repo
````
