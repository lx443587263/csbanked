# from application.ninja_cof import api
# Author 刘希
# coding=utf-8
# @Time    : 2024/7/1 21:47
# @File    : support_case.py
# @Software: PyCharm
# @qq: 443587263

from typing import List

from django.shortcuts import get_object_or_404
from ninja import Field, ModelSchema, Query, Router, Schema
from ninja.pagination import paginate
from system.models import SupportCase
from utils.fu_crud import create, delete, retrieve, update
from utils.fu_ninja import FuFilters, MyPagination
from utils.fu_response import FuResponse
from utils.list_to_tree import list_to_route, list_to_tree

router = Router()


class Filters(FuFilters):
    caseTitle: str = Field(None, alias="caseTitle")
    status: bool = Field(None, alias="status")
    id: str = Field(None, alias="id")


class SchemaIn(ModelSchema):
    id: int = None
    caseId: str = None
    caseTitle: str = None
    content: str = None
    status: str = None
    dept: int = Field(None, alias="dept")

    class Config:
        model = SupportCase
        model_fields = "__all__"


class SchemaOut(ModelSchema):
    class Config:
        model = SupportCase
        model_fields = "__all__"


@router.delete("/case/{case_id}")
def delete_case(request, case_id: int):
    delete(case_id, SupportCase)
    return {"success": True}


@router.get("/case", response=List[SchemaOut])
def all_list_case(request):
    qs = retrieve(request, SupportCase)
    return qs


@router.post("/case", response=SchemaOut)
def create_case(request, data: SchemaIn):
    case = create(request, data, SupportCase)
    return case