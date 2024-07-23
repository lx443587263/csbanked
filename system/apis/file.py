# -*- coding: utf-8 -*-
# @Time    : 2024/6/07 00:56
# @Author  : 刘希
# @FileName: file.py
# @Software: PyCharm
import os
import threading
from datetime import datetime
from typing import List
from urllib.parse import unquote
import time
from django.http import FileResponse, StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404
from fuadmin.settings import BASE_DIR, STATIC_URL
from ninja import Field
from ninja import File as NinjaFile
from ninja import ModelSchema, Query, Router, Schema
from ninja.files import UploadedFile
from ninja.pagination import paginate
from system.models import File, Users, Dept, Product, ChipType, Category, Version
from utils.fu_crud import create, delete, retrieve, update
from utils.fu_ninja import FuFilters, MyPagination
from utils.fu_response import FuResponse
import zipfile
import shutil
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, FIRST_COMPLETED, as_completed
import fitz
from threading import Lock
from typing import Union, Tuple
from reportlab.lib import units
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List
from pikepdf import Pdf, Page, Rectangle

lock = Lock()

router = Router()


class Filters(FuFilters):
    name: str = Field(None, alias="name")


class SchemaIn(Schema):
    name: str = Field(None, alias="name")
    url: str = Field(None, alias="url")


class SchemaOut(ModelSchema):
    class Config:
        model = File
        model_fields = "__all__"


@router.delete("/file/{file_id}")
def delete_file(request, file_id: int):
    os.remove(str(File.objects.get(id=file_id).url))
    delete(file_id, File)
    return {"success": True}


@router.get("/file", response=List[SchemaOut])
def list_file(request, filters: Filters = Query(...)):
    qs = retrieve(request, File, filters)
    return qs


@router.get("/file/{file_id}", response=SchemaOut)
def get_file(request, file_id: int):
    qs = get_object_or_404(File, id=file_id)
    return qs


@router.get("/file/all/list", response=List[SchemaOut])
def all_list_role(request):
    qs = retrieve(request, File)
    return qs


@router.post("/upload", response=SchemaOut)
def upload(request, file: UploadedFile = NinjaFile(...)):
    binary_data = file.read()
    current_date = datetime.now().strftime('%Y%m%d%H%M%S%f')
    current_ymd = datetime.now().strftime('%Y%m%d')
    file_name = current_date + '_' + file.name.replace(' ', '_')
    file_path = os.path.join(STATIC_URL, current_ymd)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_url = os.path.join(file_path, file_name)
    with open(file_url, 'wb') as f:
        f.write(binary_data)
    data = {
        'name': file.name,
        'size': file.size,
        'save_name': file_name,
        'url': file_url,
    }
    qs = create(request, data, File)
    return qs


@router.post("/download")
def create_post(request, data: SchemaIn):
    global def_file_list,zipfilename
    filePath = str(BASE_DIR) + unquote(data.url)
    s1 = time.time()
    newfilePath = dispose_file2(filePath, data.name, request.request_data['user_id'])
    print(time.time() - s1)
    # zip_file = zipfile.ZipFile(filePath)
    # file_list = zip_file.namelist()
    # print(file_list)
    for i in def_file_list:
        zip_del_command = "zip -d %s '%s'" % (newfilePath, i+'/[!w]*.pdf')
        os.system(zip_del_command)
    zip_del_command = "zip -d %s '%s'" % (newfilePath, zipfilename + '/filelist.txt')
    os.system(zip_del_command)
    r = FileResponse(open(newfilePath, "rb"), as_attachment=True)
    os.remove(newfilePath)
    del_file_list = []
    zipfilename = ""
    return r


@router.put("/file/{file_id}")
def updata_file(request, file_id: int):
    if request.request_data['virtual_path'] or request.request_data['name'] or request.request_data['permissions']:
        File.objects.filter(id=file_id).update(virtual_path=request.request_data['virtual_path'],
                                               name=request.request_data['name'],
                                               permissions=request.request_data['permissions']);
        return FuResponse({"state": True, "msg": "修改成功"})


@router.get("/image/{image_id}", auth=None)
def get_file(request, image_id: int):
    qs = get_object_or_404(File, id=image_id)

    return HttpResponse(open(os.path.join(str(BASE_DIR), str(qs.url)), "rb"), content_type='image/png')


def dispose_file(filePath, fileName, userId):
    if filePath.endswith('.zip'):
        # 3、解压zip文件
        test = zipfile.ZipFile(filePath)
        # 4、获取zip文件的文件名，解压到同名文件夹内
        file_name = fileName.replace('.zip', '')
        test.extractall('/tmp')
        test.close()
        # 5.1、找到txt文件
        txt_files = [filename for filename in os.listdir('/tmp/' + file_name) if
                     os.path.splitext(filename)[1] == ".txt"]
        if txt_files:
            with open('/tmp/' + file_name + '/' + txt_files[0]) as file:
                content = file.readlines()
            # content = open('/tmp/test/test/'+txt_files[0], 'r').readlines()
            # txt_files.close()
            user_obj = Users.objects.get(id=userId)
            if user_obj.username != 'superadmin':
                dept_name = Dept.objects.get(id=user_obj.dept_id).name
                email = user_obj.email
            else:
                dept_name = "superadmin"
                email = "superadmin"
            t = time.localtime(time.time())
            pdf_file_mark = create_watermark(email + "_" + dept_name + "_" + time.asctime(t), user_obj.username)
            result_list = [line.strip() for line in content]
            #######线程池###########
            all_task = []
            with ThreadPoolExecutor(max_workers=2) as pool:
                for second in result_list:
                    all_task.append(pool.submit(ff, file_name, pdf_file_mark, second))

                # 主线程等待所有子线程完成
                wait(all_task, timeout=None, return_when=ALL_COMPLETED)
                print("----complete-----")
            #######线程池###########
            # for pdfPath in result_list:
            #     add_watermark('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1], pdf_file_mark, '/tmp/'+file_name+'/pdf/warter'+os.path.split(pdfPath)[-1])
            #     # add_watermark_by_text('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1],'/tmp/'+file_name+'/pdf/warter'+os.path.split(pdfPath)[-1])
            #     # shutil.rmtree(pdf_file_mark)
            #     shutil.move('/tmp/'+file_name+'/pdf/warter'+os.path.split(pdfPath)[-1], '/tmp/'+file_name+'/'+pdfPath)
            #     os.remove('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1])
            #     # shutil.rmtree('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1])
        # 6、新建1个zip文件
        Myzip = zipfile.ZipFile('/tmp/' + file_name + '.zip', 'w')
        # 7、将文件夹内的文件遍历
        for root, dirs, files in os.walk('/tmp/' + file_name):
            for file in files:
                # 8、某些文件不需要被打包进去
                if '.py' in file or '.idea' in file or '.DS_Store' in file or '.txt' in file:
                    continue
                # 9、将文件打包进去，把目录里的文件夹内的内容打包到zip文件的根目录，而不是zip内的对应目录，这里是个细节；
                # 你可以去掉string参数。 这样就好了。 Myzip.write(os.path.join(root, file)
                string = os.path.join(root, file).replace('/tmp/' + file_name, '/')
                Myzip.write(os.path.join(root, file), string)

        Myzip.close()
        os.remove(pdf_file_mark)
        shutil.rmtree('/tmp/' + file_name)
    return '/tmp/' + file_name + '.zip'

def_file_list= []
zipfilename = ""
def dispose_file2(filePath, fileName, userId):
    global def_file_list,zipfilename
    r = zipfile.is_zipfile(filePath)
    if r:
        cp_command = "cp %s %s" % (filePath, '/tmp/' + fileName)
        if os.system(cp_command) == 0:
            fz = zipfile.ZipFile('/tmp/' + fileName, 'r')
            file_name = fileName.replace('.zip', '')
            zipfilename = file_name
            for file in fz.namelist():
                if file == file_name + '/filelist.txt':
                    fz.extract(file, '/tmp')
                    with open('/tmp/' + file_name + '/filelist.txt', 'r') as file:
                        content = file.readlines()
                        user_obj = Users.objects.get(id=userId)
                        if user_obj.username != 'superadmin':
                            if Dept.objects.get(id=user_obj.dept_id).parent_id:
                                dept_name = Dept.objects.get(id=(Dept.objects.get(id=user_obj.dept_id).parent_id)).name
                            else:
                                dept_name = Dept.objects.get(id=user_obj.dept_id).name
                            email = user_obj.email
                        else:
                            dept_name = "superadmin"
                            email = "superadmin"
                        t = time.localtime(time.time())
                        pdf_file_mark = create_watermark_pike(content=email + "_" + dept_name + "_" + time.asctime(t),
                                                              username=user_obj.username,
                                                              width=200,
                                                              height=200,
                                                              font='Helvetica',
                                                              fontsize=35,
                                                              text_fill_alpha=0.3)
                        result_list = [line.strip() for line in content]
                        def_file_list = result_list.copy()
                        #######线程池###########
                        all_task = []
                        with ThreadPoolExecutor(max_workers=10) as pool:
                            for second in result_list:
                                all_task.append(pool.submit(ff2, '/tmp/' + fileName, pdf_file_mark, second))
                            # 主线程等待所有子线程完成
                            wait(all_task, timeout=None, return_when=ALL_COMPLETED)
                            print("----complete-----")
                        #######线程池###########
                        os.remove(pdf_file_mark)
                        zf = zipfile.ZipFile('/tmp/' + fileName, "a")
                        for i in result_list:
                            # root, dirs, files
                            for root, subdirs, files in os.walk('/tmp/' + i):
                                for filename in files:
                                    zf.write(os.path.join(root, filename), i + '/' + filename, zipfile.ZIP_DEFLATED)
                        zf.close()
                    shutil.rmtree('/tmp/' + file_name)
        else:
            print("cp failed")
    else:
        print('This is not zip......')
    return '/tmp/' + fileName


def ff2(zipFilePath, pdf_file_mark, pdfPath):
    zip_command = "unzip %s '%s' -d %s " % (zipFilePath, pdfPath + '/*.pdf', '/tmp')
    if os.system(zip_command) == 0:
        templist = os.listdir('/tmp/' + pdfPath)
        zip_del_command = "zip -d %s '%s'" % (zipFilePath, pdfPath + '/[!w]*.pdf')
        if os.system(zip_del_command) == 0:
            for i in templist:
                add_watermark2('/tmp/' + pdfPath + '/' + i, pdf_file_mark, '/tmp/' + pdfPath + '/w_' + i, 3, 2, [0])
                # add_watermark('/tmp/' + pdfPath+'/'+i,pdf_file_mark,'/tmp/' + pdfPath+'/w_'+i)
                os.remove('/tmp/' + pdfPath + '/' + i)
            print('Delete success')
        else:
            print('Delete Failed')
        os.remove('/tmp/' + pdfPath + '/filelist.txt')
        print('Successful backup to /tmp')
    else:
        print('Backup FAILED')


def ff(file_name, pdf_file_mark, pdfPath):
    add_watermark('/tmp/' + file_name + '/pdf/' + os.path.split(pdfPath)[-1], pdf_file_mark,
                  '/tmp/' + file_name + '/pdf/warter' + os.path.split(pdfPath)[-1])
    # add_watermark_by_text('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1],'/tmp/'+file_name+'/pdf/warter'+os.path.split(pdfPath)[-1])
    # shutil.rmtree(pdf_file_mark)
    shutil.move('/tmp/' + file_name + '/pdf/warter' + os.path.split(pdfPath)[-1], '/tmp/' + file_name + '/' + pdfPath)
    os.remove('/tmp/' + file_name + '/pdf/' + os.path.split(pdfPath)[-1])
    # shutil.rmtree('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1])


def create_watermark(content, username):
    """水印信息"""
    # 默认大小为21cm*29.7cm
    file_name = '/tmp/' + username + '.pdf'
    c = canvas.Canvas(file_name, pagesize=(30 * cm, 30 * cm))
    # 移动坐标原点(坐标系左下为(0,0))
    c.translate(10 * cm, 5 * cm)

    # 设置字体
    c.setFont("Helvetica", 10)
    # 指定描边的颜色
    c.setStrokeColorRGB(0, 1, 0)
    # 指定填充颜色
    c.setFillColorRGB(0, 1, 0)
    # 旋转45度,坐标系被旋转
    c.rotate(30)
    # 指定填充颜色
    c.setFillColorRGB(0, 0, 0, 0.1)
    # 设置透明度,1为不透明
    # c.setFillAlpha(0.1)
    # 画几个文本,注意坐标系旋转的影响
    for i in range(5):
        for j in range(10):
            a = 10 * (i - 1)
            b = 5 * (j - 2)
            c.drawString(a * cm, b * cm, content)
            c.setFillAlpha(0.1)
    # 关闭并保存pdf文件
    c.save()
    return file_name


def add_watermark_by_text(input_path, output_path):
    """PymuPDF 矩形方案"""
    doc = fitz.open(input_path)
    t_list = []
    for page in doc:
        t = threading.Thread(target=xxx, args=(page,))
        t_list.append(t)
        t.start()

    for t in t_list:
        t.join()
    #     for i in range(3):
    #         for j in range(8):
    #             p1 = fitz.Point((page.rect.width - 400)*i, (page.rect.height - 700)*j)
    #             shape = page.new_shape()
    #             shape.draw_circle(p1, 1)
    #             shape.finish(width=0.3, color=red, fill=red)
    #             shape.insert_text(p1, text1, rotate=0, color=gray)
    #             shape.commit()
    doc.save(output_path)


def xxx(page, ):
    # lock.acquire()
    text1 = "rotate=-90"
    red = (1, 0, 0)
    gray = (0, 0, 1)
    for i in range(3):
        for j in range(8):
            p1 = fitz.Point((page.rect.width - 400) * i, (page.rect.height - 700) * j)
            shape = page.new_shape()
            shape.draw_circle(p1, 1)
            shape.finish(width=0.3, color=red, fill=red)
            shape.insert_text(p1, text1, rotate=0, color=gray)
            shape.commit()
    # lock.release()


def add_watermark(pdf_file_in, pdf_file_mark, pdf_file_out):
    """把水印添加到pdf中"""
    pdf_output = PdfFileWriter()
    input_stream = open(pdf_file_in, 'rb')
    pdf_input = PdfFileReader(input_stream, strict=False)

    # 获取PDF文件的页数
    pageNum = pdf_input.getNumPages()

    # 读入水印pdf文件
    pdf_watermark = PdfFileReader(open(pdf_file_mark, 'rb'), strict=False)
    # 给每一页打水印
    for i in range(pageNum):
        page = pdf_input.getPage(i)
        page.mergePage(pdf_watermark.getPage(0))
        page.compressContentStreams()  # 压缩内容
        pdf_output.addPage(page)
        # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        #     to_do = []
        #     for j in range(10):  # 模拟多个任务
        #         future = executor.submit(ttt, pdf_input,pdf_watermark,i)
        #         to_do.append(future)
        #
        #
        #     for future in concurrent.futures.as_completed(to_do):  # 并发执行
        #         pdf_output.addPage(future.result())

    pdf_output.write(open(pdf_file_out, 'wb'))


def ttt(pdf_input, pdf_watermark, num_pages):
    page = pdf_input.getPage(num_pages)
    page.mergePage(pdf_watermark.getPage(0))
    page.compressContentStreams()  # 压缩内容
    return page


def operate_pdf(pdfPath, userId, file_name):
    # 缺少打水印内容
    user_obj = Users.objects.get(id=userId)
    if user_obj.username != 'superadmin':
        dept_name = Dept.objects.get(id=user_obj.dept_id).name
        email = user_obj.email
    else:
        dept_name = "superadmin"
        email = "superadmin"
    t = time.localtime(time.time())
    pdf_file_mark = create_watermark(email + "_" + dept_name + "_" + time.asctime(t), user_obj.username)
    add_watermark('/tmp/' + file_name + '/pdf/' + os.path.split(pdfPath)[-1], pdf_file_mark,
                  '/tmp/' + file_name + '/pdf/warter' + os.path.split(pdfPath)[-1])
    # shutil.rmtree(pdf_file_mark)
    os.remove(pdf_file_mark)
    shutil.move('/tmp/' + file_name + '/pdf/warter' + os.path.split(pdfPath)[-1], '/tmp/' + file_name + '/' + pdfPath)
    os.remove('/tmp/' + file_name + '/pdf/' + os.path.split(pdfPath)[-1])
    # shutil.rmtree('/tmp/'+file_name+'/pdf/'+os.path.split(pdfPath)[-1])


def create_watermark_pike(content: str,
                          username: str,
                          width: Union[int, float],
                          height: Union[int, float],
                          font: str,
                          fontsize: int,
                          angle: Union[int, float] = 45,
                          text_stroke_color_rgb: Tuple[int, int, int] = (0, 0, 0),
                          text_fill_color_rgb: Tuple[int, int, int] = (0, 0, 0),
                          text_fill_alpha: Union[int, float] = 1) -> str:
    '''
    用于生成包含content文字内容的水印pdf文件
    content: 水印文本内容
    filename: 导出的水印文件名
    width: 画布宽度，单位：mm
    height: 画布高度，单位：mm
    font: 对应注册的字体代号
    fontsize: 字号大小
    angle: 旋转角度
    text_stroke_color_rgb: 文字轮廓rgb色
    text_fill_color_rgb: 文字填充rgb色
    text_fill_alpha: 文字透明度
    '''
    file_name = '/tmp/' + username + '.pdf'

    # 创建pdf文件，指定文件名及尺寸，这里以像素单位为例
    c = canvas.Canvas(f"{file_name}", pagesize=(width * units.mm, height * units.mm))

    # 进行轻微的画布平移保证文字的完整
    c.translate(0.1 * width * units.mm, 0.1 * height * units.mm)

    # 设置旋转角度
    c.rotate(angle)

    # 设置字体及字号大小
    c.setFont(font, fontsize)

    # 设置文字轮廓色彩
    c.setStrokeColorRGB(*text_stroke_color_rgb)

    # 设置文字填充色
    c.setFillColorRGB(*text_fill_color_rgb)

    # 设置文字填充色透明度
    c.setFillAlpha(text_fill_alpha)

    # 绘制文字内容
    c.drawString(0, 0, content)

    # 保存水印pdf文件
    c.save()

    return file_name


def add_watermark2(target_pdf_path: str,
                   watermark_pdf_path: str,
                   pdf_out: str,
                   nrow: int,
                   ncol: int,
                   skip_pages: List[int] = []) -> None:
    '''
    向目标pdf文件中添加平铺水印
    target_pdf_path: 目标pdf文件的路径+文件名
    watermark_pdf_path: 水印pdf文件的路径+文件名
    nrow: 水印平铺的行数
    ncol：水印平铺的列数
    skip_pages: 需要跳过不添加水印的页面序号（从0开始）
    '''

    # 读入需要添加水印的pdf文件
    target_pdf = Pdf.open(target_pdf_path)

    # 读入水印pdf文件并提取水印页
    watermark_pdf = Pdf.open(watermark_pdf_path)
    watermark_page = watermark_pdf.pages[0]

    # 遍历目标pdf文件中的所有页（排除skip_pages指定的若干页）
    for idx, target_page in enumerate(target_pdf.pages):

        if idx not in skip_pages:
            for x in range(ncol):
                for y in range(nrow):
                    # 向目标页指定范围添加水印
                    target_page.add_overlay(watermark_page, Rectangle(target_page.trimbox[2] * x / ncol,
                                                                      target_page.trimbox[3] * y / nrow,
                                                                      target_page.trimbox[2] * (x + 1) / ncol,
                                                                      target_page.trimbox[3] * (y + 1) / nrow))

    # 将添加完水印后的结果保存为新的pdf
    target_pdf.save(pdf_out)
