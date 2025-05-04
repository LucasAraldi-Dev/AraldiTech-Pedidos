from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from . import schemas, database, auth
from .auth import get_current_user
from passlib.context import CryptContext
import logging

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Função para converter ObjectId para string
def parse_obj_id(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id']) 
    return doc

# Rota para listar todos os usuários (apenas para admins)
@router.get("/usuarios", response_model=List[dict])
async def list_users(db=Depends(database.get_db), current_user=Depends(get_current_user)):
    # Verificar se o usuário atual é admin
    if current_user.get("tipo_usuario") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores"
        )
    
    # Buscar todos os usuários
    users = await db["users"].find().to_list(length=100)
    return [parse_obj_id(user) for user in users]

# Rota para atualizar um usuário (apenas para admins)
@router.put("/usuarios/{user_id}", response_model=dict)
async def update_user(user_id: str, user_data: dict, db=Depends(database.get_db), current_user=Depends(get_current_user)):
    # Verificar se o usuário atual é admin
    if current_user.get("tipo_usuario") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores"
        )
    
    # Verificar se o usuário existe
    existing_user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Preparar dados para atualização
    update_data = {k: v for k, v in user_data.items() if k not in ["_id", "log"]}
    
    # Se houver nova senha, criptografá-la
    if "senha" in update_data:
        update_data["senha"] = pwd_context.hash(update_data["senha"])
    
    # Registrar log de alterações
    if "log" in user_data:
        # Se já existir um histórico de logs, adicionar o novo log
        if "logs" in existing_user:
            update_data["logs"] = existing_user["logs"] + [user_data["log"]]
        else:
            update_data["logs"] = [user_data["log"]]
    
    # Atualizar o usuário
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Retornar o usuário atualizado
    updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
    return parse_obj_id(updated_user)

# Rota para obter logs de alterações de um usuário (apenas para admins)
@router.get("/usuarios/{user_id}/logs", response_model=List[dict])
async def get_user_logs(user_id: str, db=Depends(database.get_db), current_user=Depends(get_current_user)):
    # Verificar se o usuário atual é admin
    if current_user.get("tipo_usuario") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores"
        )
    
    # Verificar se o usuário existe
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Retornar logs se existirem
    return user.get("logs", [])