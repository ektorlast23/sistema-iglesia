# Matriz de permisos por rol — Sistema Iglesia (Semana 2)
Estado: PROPUESTA pendiente de validación y firma con la institución.
El documento original no especifica permisos concretos: no implementar sin esta firma.

## Roles
- **Administrador**: acceso total, configura el sistema y crea usuarios.
- **Secretaría**: opera miembros, eventos y asistencia. Sin usuarios ni inventario.
- **Encargado de inventario**: opera equipos y mantenimiento. Sin miembros ni usuarios.

## Matriz (✅ permitido / ❌ denegado / 🔒 acotado)

| Caso de uso | Administrador | Secretaría | Encargado inventario |
|---|---|---|---|
| Iniciar sesión | ✅ | ✅ | ✅ |
| Gestionar usuarios (crear/bloquear) | ✅ | ❌ | ❌ |
| Gestionar miembros + familias + ministerios | ✅ todo | ✅ crear/editar, ❌ eliminar | ❌ |
| Gestionar eventos | ✅ todo | ✅ crear/editar, ❌ eliminar | ❌ |
| Registrar asistencia | ✅ | ✅ | ❌ |
| Gestionar inventario (equipos) | ✅ todo | ❌ | ✅ crear/editar, ❌ eliminar |
| Registrar mantenimiento | ✅ | ❌ | ✅ |
| Consultar reportes | ✅ todos | 🔒 solo asistencia/miembros | 🔒 solo inventario |

## Reglas de negocio a confirmar
1. ¿Secretaría puede ELIMINAR miembros/eventos o solo crear/editar?
2. ¿Encargado puede ELIMINAR equipos o solo crear/editar + mantenimiento?
3. ¿Reportes de Secretaría incluyen datos demográficos o solo listas de asistencia?
4. ¿Administrador es el pastor, un diácono o personal TI? (define quién firma la entrega Sem 15).

## Relaciones include/extend
- `Gestionar eventos <<include>> Registrar asistencia` (todo evento permite pasar lista).
- `Consultar reportes <<extend>> Gestionar miembros` y `<<extend>> Gestionar inventario`.
- Todo caso requiere `Iniciar sesión` previo.

## Archivos
- `casos-uso-corregido.mmd` / `.png` — diagrama corregido con frontera del sistema.
- `diagrama de casosUsoInicial.png` — versión original observada (doble flecha a inventario, sin login ni mantenimiento, Secretaría sin miembros).
