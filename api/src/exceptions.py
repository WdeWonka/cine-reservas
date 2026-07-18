from fastapi import status


class AppError(Exception):
    """Excepción de negocio base para toda la app. Cada subclase define su
    propio status_code — el handler global en main.py lo usa directo,
    sin necesitar un mapeo por tipo en cada router."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
