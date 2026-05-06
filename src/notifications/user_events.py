"""Handlers for user domain events — invoked from EventBridge Lambda."""

import typing

from src.shared_kernel.application.ports import email_service as email_port


async def handle_user_registered(
    detail: dict[str, typing.Any],
    email_svc: email_port.AbstractEmailService,
) -> None:
    first_name: str = detail.get("first_name", "")
    email: str = detail["email"]
    await email_svc.send(
        email_port.EmailMessage(
            to=email,
            subject="Bienvenido a AgroConecta",
            html_body=_welcome_html(first_name),
            text_body=(
                f"Hola {first_name}, bienvenido a AgroConecta. "
                "Tu cuenta ha sido creada exitosamente."
            ),
        )
    )


def _welcome_html(first_name: str) -> str:
    return f"""
    <html>
      <body>
        <h1>Hola {first_name}</h1>
        <p>Tu cuenta en <strong>AgroConecta</strong> ha sido creada exitosamente.</p>
        <p>Ya puedes explorar nuestro catálogo de productos agrícolas certificados
           y conectar con agricultores de todo el país.</p>
        <p><a href="https://agroconecta.co">Ir a AgroConecta</a></p>
      </body>
    </html>
    """
