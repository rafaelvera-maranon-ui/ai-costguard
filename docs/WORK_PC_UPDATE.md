# Actualizar ai-costguard en un PC de empresa

Este procedimiento sirve para actualizar una instalacion local de `ai-costguard` en un PC corporativo cuando el codigo llega a traves de un fork empresarial.

Flujo recomendado:

```text
Repo personal actualizado
  -> Sync fork en GitHub empresa
  -> git pull en repo local empresa
  -> uv sync
  -> validaciones offline
```

## 1. Objetivo

Actualizar `ai-costguard` en el PC corporativo sin modificar repos de cliente, sin tocar configuracion real innecesariamente y sin consumir tokens LLM.

Las validaciones de este documento son offline: comprueban CLI, reglas, entorno, tests y estado local. No deben llamar a Cline, Claude Code ni a Generative Engine.

## 2. Supuestos

- El repo local de empresa esta en una carpeta tipo:

```text
C:\Users\<usuario>\...\Github\AI\ai-costguard
```

- `origin` apunta al fork corporativo, no necesariamente al repo personal/original.
- El fork corporativo se sincroniza desde GitHub web usando `Sync fork`.
- El proyecto usa `uv`.
- No se recomienda usar `pip` directamente para este flujo.
- No ejecutes este procedimiento dentro de un repo cliente como `databricks-free-lab`.

## 3. Sincronizar fork corporativo

1. Abre el fork corporativo de `ai-costguard` en GitHub.
2. Pulsa `Sync fork`.
3. Pulsa `Update branch`.
4. Confirma que el fork queda actualizado con el repo personal/original.

No hace falta configurar un upstream local para este flujo. La sincronizacion se hace desde GitHub web para reducir pasos y evitar confusiones en el PC de empresa.

## 4. Actualizar repo local

Abre PowerShell y situa la terminal en el repo local de `ai-costguard`, no en un repo cliente:

```powershell
Set-Location "RUTA_AL_REPO\ai-costguard"

git remote -v
git status
git branch --show-current

git fetch origin --prune
git pull --ff-only origin main
git log --oneline -10
```

Evidencia esperada:

- `origin` apunta al fork corporativo.
- La rama activa es `main`.
- `git status` no muestra cambios locales pendientes antes de actualizar.
- `git pull --ff-only origin main` termina sin merge manual.
- `git log --oneline -10` muestra commits recientes esperados.

Si `git pull --ff-only` falla por cambios locales, no ejecutes `git reset --hard` sin backup y sin entender que cambios se perderian.

## 5. Parar CostGuard antes de actualizar entorno

Antes de recrear `.venv`, para CostGuard si estaba arrancado:

```powershell
costguard stop

Get-Process python,uv,costguard -ErrorAction SilentlyContinue | Select-Object Name,Id,Path
```

Interpretacion:

- Si no devuelve procesos, se puede continuar.
- Si devuelve procesos `python`, `costguard` o `uv`, pueden estar bloqueando `.venv`.
- No mates procesos a ciegas. Comprueba la ruta `Path` y confirma que pertenecen a este repo o a CostGuard antes de cerrarlos.

## 6. Recrear entorno limpio con uv

Desde el repo local de `ai-costguard`:

```powershell
Remove-Item -Recurse -Force .\.venv

uv sync --extra dev --extra headroom
```

Usamos recreacion limpia porque en pruebas reales ha evitado problemas de entornos inconsistentes, `missing RECORD file`, paquetes a medio instalar y errores de `Acceso denegado`.

Evidencia esperada:

- Aparece algo equivalente a `Creating virtual environment at: .venv`.
- Se instalan paquetes desde el proyecto local.
- `ai-costguard` queda instalado desde una ruta tipo `file:///.../ai-costguard`.
- `headroom-ai` aparece instalado si se usa el extra `headroom`.
- No aparecen warnings tipo `missing RECORD file`.
- No aparecen errores de `Acceso denegado`.

Si `Remove-Item` falla, vuelve a la seccion anterior y revisa procesos vivos.

## 7. Validar CLI actualizada

```powershell
uv run costguard --help
```

Comandos esperados:

- `setup`
- `start`
- `stop`
- `status`
- `doctor`
- `cline-config`
- `budget`
- `rules`
- `usage`
- `cache`
- `headroom`
- `pricing`

Si `costguard` no aparece, usa siempre `uv run costguard ...` dentro del repo y evita mezclar con instalaciones globales antiguas.

## 8. Validaciones offline sin consumir tokens

Estas validaciones no deben llamar a LLMs ni consumir cuota de Generative Engine:

```powershell
uv run pytest

uv run costguard rules test "cat .env"
uv run costguard rules test "git diff"
uv run costguard rules test "find ."

uv run costguard pricing --help
uv run costguard pricing status

uv run costguard headroom status
uv run costguard cache status
```

Evidencia esperada:

- `pytest` pasa.
- `cat .env` queda bloqueado.
- `git diff` y `find .` se reescriben a comandos mas pequenos.
- `pricing status`, `headroom status` y `cache status` muestran estado local.

No pruebes Cline contra el modelo durante esta fase si la cuota esta agotada o si solo quieres validar la actualizacion local.

## 9. Validacion aislada opcional

Para validar `setup` sin tocar `~/.costguard`, `~/.claude` ni configuracion real de Claude Code, usa rutas temporales dentro del repo:

```powershell
$env:COSTGUARD_HOME = "$(Get-Location)\.tmp\costguard"
$env:COSTGUARD_CLAUDE_HOME = "$(Get-Location)\.tmp\claude"

uv run costguard setup --tool cline --daily-budget 5 --monthly-budget 100 --budget-mode warn --non-interactive
uv run costguard doctor
uv run costguard status
uv run costguard cline-config
```

Esta validacion aislada no debe modificar configuracion real de Claude Code. Al usar `--tool cline`, CostGuard solo imprime configuracion para Cline y mantiene la prueba dentro de `COSTGUARD_HOME`.

## 10. Que no hacer

- No ejecutes este procedimiento dentro de repos cliente.
- No uses `pip install` directamente salvo que un runbook especifico lo indique.
- No ejecutes `git reset --hard` sin backup.
- No toques `~/.claude/settings.json` sin confirmacion explicita.
- No pegues secretos en terminal, issues, logs ni chats.
- No pruebes Cline contra el modelo si la cuota de Generative Engine esta agotada.
- No uses `Retry` en Cline si aparece `payload blocked by secret filter`; usa `Start New Task`.

## 11. Troubleshooting

### Caso: `uv sync` falla con `Acceso denegado`

Para CostGuard:

```powershell
costguard stop
```

Comprueba procesos:

```powershell
Get-Process python,uv,costguard -ErrorAction SilentlyContinue | Select-Object Name,Id,Path
```

Si no hay procesos relevantes, borra `.venv` y repite `uv sync`:

```powershell
Remove-Item -Recurse -Force .\.venv
uv sync --extra dev --extra headroom
```

### Caso: warning `missing RECORD file`

Recrea `.venv` con `uv`:

```powershell
Remove-Item -Recurse -Force .\.venv
uv sync --extra dev --extra headroom
```

### Caso: `pip` no existe en `.venv`

Es esperado si el entorno se gestiona con `uv`. Usa:

```powershell
uv run costguard --help
uv run pytest
```

### Caso: `429 true` desde Cline

Suele ser limite o cuota del proveedor Generative Engine, no necesariamente un bloqueo de CostGuard.

Acciones posibles:

- Esperar al reset de cuota.
- Cambiar credenciales o tier si aplica.
- Validar offline con `uv run pytest` y comandos `costguard` sin llamar al modelo.

### Caso: `payload blocked by secret filter`

Puede deberse a contexto acumulado en Cline.

Acciones recomendadas:

- Abre `Start New Task`.
- Prueba un prompt minimo como `Di OK`.
- No uses `Retry` como primer diagnostico, porque puede reenviar el mismo contexto acumulado.

## 12. Checklist final

- [ ] Fork corporativo sincronizado desde GitHub.
- [ ] Repo local actualizado con `git pull --ff-only`.
- [ ] `costguard stop` ejecutado.
- [ ] Sin procesos `python`, `uv` o `costguard` bloqueando.
- [ ] `.venv` recreado con `uv`.
- [ ] `uv run costguard --help` muestra `pricing`, `headroom` y `cache`.
- [ ] `pytest` pasa.
- [ ] `rules test` funciona.
- [ ] `pricing status` funciona.
- [ ] No se tocaron repos cliente.
- [ ] No se consumieron tokens LLM durante validaciones offline.
