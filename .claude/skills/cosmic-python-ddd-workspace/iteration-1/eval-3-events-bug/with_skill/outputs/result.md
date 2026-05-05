# Eval 3 WITH SKILL — Bug: eventos publicados antes del commit

## El código actual YA es correcto

`src/identity/user/application/handlers/commands.py` líneas 87-90:
```python
        await uow.commit()
        pending_events = list(uow.collect_new_events())   # DENTRO del async with

    await publisher.publish_many(pending_events)           # FUERA del async with
```

## Por qué ocurre el bug — las 3 causas raíz

### Causa 1 — Invertir commit y collect (la más común)
```python
# BUG
async with user_uow.UserUnitOfWork(session) as uow:
    user = user_aggregates.User.register(...)
    await uow.users.put(user)
    pending_events = list(uow.collect_new_events())  # ← eventos salen al mundo
    await publisher.publish_many(pending_events)     # ← consumidor lee BD pero usuario NO EXISTE AÚN
    await uow.commit()  # ← el usuario se guarda AQUÍ
```

### Causa 2 — collect fuera del bloque async with
```python
# BUG
async with user_uow.UserUnitOfWork(session) as uow:
    ...
    await uow.commit()
# __aexit__ — repo._seen puede quedar inválido

pending_events = list(uow.collect_new_events())  # ← puede retornar lista vacía
```

### Causa 3 — publish dentro del bloque (error de rollback)
```python
# BUG
async with user_uow.UserUnitOfWork(session) as uow:
    await uow.commit()
    pending_events = list(uow.collect_new_events())
    await publisher.publish_many(pending_events)  # ← si falla, __aexit__ intenta rollback de sesión ya commiteada
```

## Cómo funciona internamente el patrón pull-and-clear

```
User.register() → self.record_event(UserRegistered(...))
                         ↓
              aggregate._domain_events = [UserRegistered]
                         ↓
              uow.users.put(user) → self._seen.add(user)
                         ↓
              await uow.commit() → DB PERSISTE (usuario existe en BD)
                         ↓
              uow.collect_new_events()
              → itera repo._seen
              → llama aggregate.pull_events()
              → pull_events() retorna lista Y la borra (_domain_events.clear())
                         ↓
              pending_events = [UserRegistered]
```

`collect_new_events()` va DENTRO del `async with` porque necesita `uow.users._seen`.
`publish_many()` va FUERA porque si falla, no debe hacer rollback del commit ya confirmado.

## Código correcto completo

```python
async def handle_register(
    command: inputs.RegisterInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    settings: app_config.Settings,
    publisher: event_publisher_port.AbstractEventPublisher,
) -> outputs.AuthOutput:
    async with user_uow.UserUnitOfWork(session) as uow:
        # 1. Validar
        existing = await uow.users.find_by_email(user_value_objects.Email(value=command.email))
        if existing is not None:
            raise user_exceptions.EmailAlreadyExistsError(command.email)

        # 2. Dominio
        user = user_aggregates.User.register(...)

        # 3. Persistir
        await uow.users.put(user)
        await uow.commit()  # ← BD confirma PRIMERO

        # 4. Recolectar DENTRO del async with (repo._seen aún válido)
        pending_events = list(uow.collect_new_events())

    # 5. Publicar FUERA del async with (BD ya consistente)
    await publisher.publish_many(pending_events)

    return outputs.AuthOutput(...)
```

## Tabla resumen

| Paso | Dónde | Por qué |
|------|-------|---------|
| `uow.commit()` | Dentro del `async with` | Confirma la transacción |
| `uow.collect_new_events()` | Dentro del `async with`, después del commit | `repo._seen` válido; borra eventos del agregado |
| `publisher.publish_many()` | Fuera del `async with` | BD ya consistente; si falla, el dato está seguro |
