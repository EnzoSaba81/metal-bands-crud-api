import os
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from dotenv import load_dotenv 
from typing import Annotated
from sqlmodel import Field, Session, create_engine, select, SQLModel


app = FastAPI()

bandas = [
    {"id":0, "nombre": "Metallica", "genero": "Metal", "pais": "Estados Unidos"},
    {"id":1, "nombre": "Black Sabbath","genero": "Black Metal", "pais": "Reino Unido"},
    {"id":2, "nombre": "Iron Maiden", "genero": "Heavy Metal", "pais": "Reino Unido"},
    {"id":3, "nombre": "Slayer", "genero": "Thrash Metal", "pais": "Estados Unidos"},
]

load_dotenv()  # Carga las variables de entorno desde el archivo .env

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Configuración de la conexión a la base de datos
url_conecction = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
) 

engine = create_engine(url_conecction)


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

@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # Crea la base de datos y las tablas si no existen

@app.get("/bandas/")
def list_bandas(limit: int | None = None):
    if limit is None:
        return bandas
    else:
        return bandas[0:limit]

@app.get("/bandas/{banda_id}")
def get_banda(banda_id : int):
    for banda in bandas:  # esto hace que busque en la lista de bandas y chequee si hay una con ese id
        if banda["id"] == banda_id:
            return banda
    raise HTTPException(status_code=404, detail="Banda no encontrada")


@app.post("/bandas/")
async def create_banda(banda: Banda):
    new_id = bandas[-1]["id"] + 1 if bandas else 0
    
    nueva_banda_dict= banda.model_dump() # Convierte el objeto Pydantic a un diccionario 
    
    nueva_banda_dict["id"] = new_id # Agrega el nuevo id a la banda
    
    bandas.append(nueva_banda_dict) # Agrega la nueva banda a la lista de bandas
    
    return {"Mensaje": "Banda creada exitosamente", "banda": nueva_banda_dict}

@app.put("/bandas/{banda_id}")
async def update_banda(banda_id: int, banda_update: Banda):
    for banda in bandas:
        if banda["id"] == banda_id:
            datos_actualizados = banda_update.model_dump()  # Convierte el objeto Pydantic a un diccionario
            
            banda.update(datos_actualizados)
            
            banda["id"] = banda_id  # Asegura que el id no se pierda durante la actualización
            return {"Mensaje": "Banda actualizada exitosamente", "banda": banda}
    
    raise HTTPException(status_code=404, detail="Banda no encontrada")


@app.delete("/bandas/{banda_id}")
async def delete_banda(banda_id: int):
    for banda in bandas:
        if banda["id"] == banda_id:
            bandas.remove(banda)
            return {"Mensaje": "Banda eliminada exitosamente"}
        
    raise HTTPException(status_code=404, detail="Banda no encontrada")


