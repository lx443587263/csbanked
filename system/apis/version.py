# from application.ninja_cof import api
# Author 刘希
# coding=utf-8
# @Time    : 2024/5/15 21:47
# @File    : dept.py
# @Software: PyCharm
# @qq: 443587263

from typing import List

from django.shortcuts import get_object_or_404,get_list_or_404
from ninja import Field, ModelSchema, Query, Router, Schema
from ninja.pagination import paginate
from system.models import ChipType,Product,Category,Version
from utils.fu_crud import create, delete, retrieve, update
from utils.fu_ninja import FuFilters, MyPagination
from utils.fu_response import FuResponse
from utils.list_to_tree import list_to_route, list_to_tree

router = Router()

class VersionFilters(FuFilters):
    name: str = Field(None, alias="name")
    id: str = Field(None, alias="id")
    product_id: str = Field(None, alias="product_id")
    chipType_id: str = Field(None,alias='chipType_id')
    category_id: str = Field(None,alias='category_id')

class VersionSchemaIn(ModelSchema):
    id: int = None
    product_id: int = None
    chipType_id: int = None
    category_id: int = None
    name: str = None

    class Config:
        model = Version
        model_exclude = ['id', 'name', 'product_id', 'chipType_id','category_id']


class VersionSchemaOut(ModelSchema):
    class Config:
        model = Version
        model_fields = "__all__"


@router.post("/version", response=VersionSchemaOut)
def create_version(request, data: VersionSchemaIn):
    data.product_id = Product.objects.get(id=data.product_id)
    data.chipType_id = ChipType.objects.get(id=data.chipType_id)
    data.category_id = Category.objects.get(id=data.category_id)
    version = create(request, data, Version)
    return version


@router.delete("/version/{version_id}")
def delete_version(request, version_id: int):
    delete(version_id, Version)
    return {"success": True}


@router.put("/version/{version_id}", response=VersionSchemaOut)
def update_version(request, version_id: int, data: VersionSchemaIn):
    data.product_id = Product.objects.get(id=data.product_id)
    data.chipType_id = ChipType.objects.get(id=data.chipType_id)
    data.category_id = Category.objects.get(id=data.category_id)
    version = update(request, version_id, data, Version)
    return version


@router.get("/version", response=List[VersionSchemaOut])
def list_version(request, filters: VersionFilters = Query(...)):
    qs = retrieve(request, Version, filters)
    return qs


@router.get("/version/{version_id}", response=VersionSchemaOut)
def get_version(request, version_id: int):
    version = get_object_or_404(Version, id=version_id)
    return version


@router.get("/version/list/{category_id}",response=List[VersionSchemaOut])
def list_version(request, category_id: int,):
    qs = list(Version.objects.filter(category_id=category_id))
    # qs = get_list_or_404(Version, chipType_id=category_id)
    return qs