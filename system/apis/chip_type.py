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
from system.models import ChipType,Product
from utils.fu_crud import create, delete, retrieve, update
from utils.fu_ninja import FuFilters, MyPagination
from utils.fu_response import FuResponse
from utils.list_to_tree import list_to_route, list_to_tree

router = Router()


class ChipTypeFilters(FuFilters):
    name: str = Field(None, alias="name")
    id: str = Field(None, alias="id")
    product_id: str = Field(None, alias="product_id")


class ChipTypeSchemaIn(ModelSchema):
    id: int = None
    product_id: int = None
    name: str = None
    class Config:
        model = ChipType
        model_exclude = ['id', 'name', 'product_id']


class ChipTypeSchemaOut(ModelSchema):
    class Config:
        model = ChipType
        model_fields = "__all__"


@router.post("/chipType", response=ChipTypeSchemaOut)
def create_chip_type(request, data: ChipTypeSchemaIn):
    data.product_id = Product.objects.get(id=data.product_id)
    chipType = create(request, data, ChipType)
    return chipType


@router.delete("/chipType/{chipType_id}")
def delete_chip_type(request, chipType_id: int):
    delete(chipType_id, ChipType)
    return {"success": True}


@router.put("/chipType/{chipType_id}", response=ChipTypeSchemaOut)
def update_chip_type(request, chipType_id: int, data: ChipTypeSchemaIn):
    data.product_id = Product.objects.get(id=data.product_id)
    chipType = update(request, chipType_id, data, ChipType)
    return chipType


@router.get("/chipType", response=List[ChipTypeSchemaOut])
def list_chip_type(request, filters: ChipTypeFilters = Query(...)):
    qs = retrieve(request, ChipType, filters)
    return qs


@router.get("/chipType/{chipType_id}", response=ChipTypeSchemaOut)
def get_chip_type(request, chipType_id: int):
    chipType = get_object_or_404(ChipType, id=chipType_id)
    return chipType

@router.get("/chipType/list/{product_id}",response=List[ChipTypeSchemaOut])
def list_chip_type(request, product_id: int,):
    qs = list(ChipType.objects.filter(product_id=product_id))
    # qs = get_list_or_404(ChipType, product_id=product_id)
    return qs