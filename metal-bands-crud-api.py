import os
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from dotenv import load_dotenv 
from typing import Annotated
from sqlmodel import Field, Session, create_engine, select, SQLModel


load_dotenv()  # Carga las variables de entorno desde el archivo .env

# Lee directamente la URL de conexión completa desde el archivo .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Creamos el engine usando la URL que viene del .env
engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Lo que hace es crear una sesion de una base de datos 
def get_session(): 
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]  # Esto es para que se pueda inyectar la sesion en los endpoints

# Creo una clase que hereda de SQLModel para poder mapear la tabla de la base de datos
class Bandabase(SQLModel):
    nombre: str
    genero: str
    pais: str


class Banda(Bandabase, table=True):
    id: int = Field(default=None, primary_key=True)  # Esto es para que sea la clave primaria y se autoincremente

class BandaPublic(Bandabase):
    id: int

class Bandacreate(Bandabase):
    pass


class Bandaupdate(Bandabase):
    nombre : str | None = None
    genero : str | None = None
    pais : str | None = None
    
    

app = FastAPI(title="API CRUD de Bandas de Metal", description="Una API para gestionar bandas de metal", version="1.0.0")



@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # Crea la base de datos y las tablas si no existen



#endpoint crear banda

@app.post("/bandas/", response_model=BandaPublic)
def create_banda(banda: Bandacreate, session: SessionDep):
    db_banda = Banda.model_validate(banda)  # Convierte el objeto Pydantic a un objeto SQLModel
    session.add(db_banda)
    session.commit()
    session.refresh(db_banda)
    return db_banda

#endpoint para listar bandas segund id

@app.get("/bandas/{banda_id}", response_model=BandaPublic)
def leer_banda(banda_id: int, session: SessionDep):
    banda = session.get(Banda, banda_id)
    if not banda:
        raise HTTPException(status_code=404, detail="Banda no encontrada")
    return banda


# endopoint para actualizar banda

@app.patch("/bandas/{banda_id}", response_model=BandaPublic)
def actualiza_banda(banda_id: int, banda_update: Bandaupdate, session: SessionDep):
    banda_db = session.get(Banda, banda_id)
    if not banda_db:
        raise HTTPException(status_code=404, detail="Banda no encontrada")
    
    datos_actualizados = banda_update.model_dump(exclude_unset=True)  # Convierte el objeto Pydantic a un diccionario y excluye los campos no establecidos
    banda_db.sqlmodel_update(datos_actualizados)  # Actualiza el objeto SQLModel con los datos del diccionario
    
    session.add(banda_db)
    session.commit()
    session.refresh(banda_db)
    return banda_db



#endpoint para listar bandas

@app.get("/bandas/", response_model=list[BandaPublic])
def leer_bandas(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 10
):
    bandas= session.exec(select(Banda).offset(offset).limit(limit)).all()
    return bandas


#endpoint para eliminar banda

@app.delete("/bandas/{banda_id}")
def delete_banda(banda_id: int, session: SessionDep):
    banda = session.get (Banda, banda_id)
    if not banda:
        raise HTTPException(status_code=404, detail="Banda no encontrada")
    
    session.delete(banda)
    session.commit()
    return{"ok": True, "message": "Banda eliminada correctamente"}


