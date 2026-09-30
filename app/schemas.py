from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class RegistroCuenta(Strict):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    clave: str = Field(min_length=12, max_length=128)


class Ingreso(Strict):
    correo: EmailStr
    clave: str


class PerfilEntrada(Strict):
    edad: int = Field(ge=18, le=120)
    talla_m: float = Field(ge=0.8, le=2.5)
    peso_kg: float = Field(gt=0, le=500)
    objetivo: str = Field(min_length=3, max_length=240)


class MedicionEntrada(Strict):
    fecha: date
    peso_kg: float = Field(gt=0, le=500)

    @field_validator("fecha")
    @classmethod
    def validar_fecha(cls, value: date) -> date:
        return fecha_valida(value)


class RegistroEntrada(Strict):
    ejercicio_id: int = Field(gt=0)
    series: int = Field(ge=1, le=50)
    repeticiones: int = Field(ge=1, le=100)
    carga_kg: float = Field(ge=0, le=1000)


class SesionEntrada(Strict):
    fecha: date
    registros: list[RegistroEntrada] = Field(min_length=1, max_length=30)

    @field_validator("fecha")
    @classmethod
    def validar_fecha(cls, value: date) -> date:
        return fecha_valida(value)


class MetaEntrada(Strict):
    carga_objetivo_kg: float = Field(gt=0, le=1000)


def fecha_valida(value: date) -> date:
    if value > date.today():
        raise ValueError("La fecha no puede estar en el futuro")
    return value
