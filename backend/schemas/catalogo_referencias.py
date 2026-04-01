from pydantic import BaseModel
from typing import Optional

# Canal Venda
class CanalVendaBase(BaseModel):
    tipo: Optional[str] = None
    linha: Optional[str] = None

class CanalVendaCreate(CanalVendaBase):
    pass

class CanalVendaUpdate(CanalVendaBase):
    pass

class CanalVendaResponse(CanalVendaBase):
    Id: int

    class Config:
        from_attributes = True

# Cidade Supervisor
class CidadeSupervisorBase(BaseModel):
    numero_supervisor_insumos: Optional[float] = None
    numero_supervisor_pet: Optional[float] = None
    nome_supervisor_pet: Optional[str] = None
    nome_supervisor_insumos: Optional[str] = None
    cidades: Optional[str] = None
    uf: Optional[str] = None

class CidadeSupervisorCreate(CidadeSupervisorBase):
    pass

class CidadeSupervisorUpdate(CidadeSupervisorBase):
    pass

class CidadeSupervisorResponse(CidadeSupervisorBase):
    codigo: int

    class Config:
        from_attributes = True

# Municipio Rota
class MunicipioRotaBase(BaseModel):
    rota: Optional[int] = None
    municipio: Optional[str] = None
    km: Optional[str] = None

class MunicipioRotaCreate(MunicipioRotaBase):
    pass

class MunicipioRotaUpdate(MunicipioRotaBase):
    pass

class MunicipioRotaResponse(MunicipioRotaBase):
    id: int

    class Config:
        from_attributes = True

# Referencias
class ReferenciasBase(BaseModel):
    empresa: Optional[str] = None
    cidade: Optional[str] = None
    telefone: Optional[str] = None
    contato: Optional[str] = None

class ReferenciasCreate(ReferenciasBase):
    pass

class ReferenciasUpdate(ReferenciasBase):
    pass

class ReferenciasResponse(ReferenciasBase):
    codigo: int

    class Config:
        from_attributes = True

# Supervisores
class SupervisoresBase(BaseModel):
    codigo: Optional[float] = None
    supervisores: Optional[str] = None
    tipo: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class SupervisoresCreate(SupervisoresBase):
    pass

class SupervisoresUpdate(SupervisoresBase):
    pass

class SupervisoresResponse(SupervisoresBase):
    id: int

    class Config:
        from_attributes = True
