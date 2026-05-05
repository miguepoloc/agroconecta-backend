# Eval 3 WITHOUT SKILL — Bug: eventos publicados antes del commit

## Causa del bug

En Cosmic Python, el patrón correcto es commit → collect_events → publish. El bug ocurre cuando se invierte el orden.

## Explicación general

Al registrar un usuario, el flujo debe garantizar que el evento `UserRegistered` solo se publique DESPUÉS de que el commit de la base de datos haya sido exitoso. Si se publica antes, hay riesgo de inconsistencia: el mundo exterior cree que el usuario existe, pero la DB podría fallar después.

## Patrón incorrecto (bug)

```python
async with uow:
    user = User.register(...)
    uow.repo.put(user)
    
    # MAL: publicando ANTES del commit
    events = uow.collect_new_events()
    publish(events)
    
    await uow.commit()
```

## Patrón correcto

```python
async with uow:
    user = User.register(...)
    uow.repo.put(user)
    await uow.commit()              # commit PRIMERO
    events = list(uow.collect_new_events())  # collect dentro

publish(events)                     # publish FUERA
```

## Diferencias vs. versión con skill

- Sin skill dio una explicación más genérica sin mencionar el rol específico de `self._seen` en el repository
- Sin skill no explicó por qué `collect_new_events()` debe estar DENTRO del `async with` (acceso a repo._seen)
- Sin skill no mencionó el riesgo de rollback si `publish_many()` va dentro del bloque
- Sin skill no mostró las 3 causas raíz del bug con código específico del proyecto
- La versión con skill fue notablemente más completa y precisa sobre los internos del patrón
