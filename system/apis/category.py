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
from system.models import ChipType,Product,Category
from utils.fu_crud import create, delete, retrieve, update
from utils.fu_ninja import FuFilters, MyPagination
from utils.fu_response import FuResponse
from utils.list_to_tree import list_to_route, list_to_tree

router = Router()

class CategoryFilters(FuFilters):
    name: str = Field(None, alias="name")
    id: str = Field(None, alias="id")
    product_id: str = Field(None, alias="product_id")
    chipType_id: str = Field(None,alias='chipType_id')

class CategorySchemaIn(ModelSchema):
    id: int = None
    product_id: int = None
    chipType_id: int = None
    name: str = None
    class Config:
        model = Category
        model_exclude = ['id', 'name', 'product_id', 'chipType_id']


class CategorySchemaOut(ModelSchema):
    class Config:
        model = Category
        model_fields = "__all__"


@router.post("/category", response=CategorySchemaOut)
def create_category(request, data: CategorySchemaIn):
    data.product_id = Product.objects.get(id=data.product_id)
    data.chipType_id = ChipType.objects.get(id=data.chipType_id)
    category = create(request, data, Category)
    return category


@router.delete("/category/{category_id}")
def delete_category(request, category_id: int):
    delete(category_id, Category)
    return {"success": True}


@router.put("/category/{category_id}", response=CategorySchemaOut)
def update_category(request, category_id: int, data: CategorySchemaIn):
    data.product_id = Product.objects.get(id=data.product_id)
    data.chipType_id = ChipType.objects.get(id=data.chipType_id)
    category = update(request, category_id, data, Category)
    return category


@router.get("/category", response=List[CategorySchemaOut])
def list_category(request, filters: CategoryFilters = Query(...)):
    qs = retrieve(request, Category, filters)
    return qs


@router.get("/category/{category_id}", response=CategorySchemaOut)
def get_category(request, category_id: int):
    category = get_object_or_404(Category, id=category_id)
    return category


@router.get("/category/list/{chipType_id}",response=List[CategorySchemaOut])
def list_category(request, chipType_id: int,):
    qs = list(Category.objects.filter(chipType_id=chipType_id))
    # qs = get_list_or_404(Category, chipType_id=chipType_id)
    return qs

