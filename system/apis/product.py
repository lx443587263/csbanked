# from application.ninja_cof import api
# Author 刘希
# coding=utf-8
# @Time    : 2024/5/15 21:47
# @File    : dept.py
# @Software: PyCharm
# @qq: 443587263

from typing import List

from django.shortcuts import get_object_or_404
from ninja import Field, ModelSchema, Query, Router, Schema
from ninja.pagination import paginate
from system.models import Product, ChipType, Category, Version
from utils.fu_crud import create, delete, retrieve, update
from utils.fu_ninja import FuFilters, MyPagination


router = Router()


class ProductFilters(FuFilters):
    name: str = Field(None, alias="name")
    id: str = Field(None, alias="id")


class ProductSchemaIn(ModelSchema):
    id: int = None
    name: str = None
    class Config:
        model = Product
        model_exclude = ['id', 'name']


class ProductSchemaOut(ModelSchema):
    class Config:
        model = Product
        model_fields = "__all__"


@router.post("/product", response=ProductSchemaOut)
def create_product(request, data: ProductSchemaIn):
    product = create(request, data, Product)
    return product


@router.delete("/product/{product_id}")
def delete_product(request, product_id: int):
    delete(product_id, Product)
    return {"success": True}


@router.put("/product/{product_id}", response=ProductSchemaOut)
def update_product(request, product_id: int, data: ProductSchemaIn):
    product = update(request, product_id, data, Product)
    return product


@router.get("/product", response=List[ProductSchemaOut])
def list_product(request, filters: ProductFilters = Query(...)):
    qs = retrieve(request, Product, filters)
    return qs



@router.get("/product/{product_id}", response=ProductSchemaOut)
def get_product(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    return product



