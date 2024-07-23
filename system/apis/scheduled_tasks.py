from ninja import Field, ModelSchema, Router, Schema
from system.models import ScheduledTasks
from utils.fu_crud import create
import requests
import json

router = Router()


class instanceSchema(Schema):
    instanceId: str = Field(None, alias="instanceId")


class ScheduledTaskSchemaIn(ModelSchema):
    id: int = None
    instanceId: str = None
    changeData: str = None
    tasksType: str = None

    class Config:
        model = ScheduledTasks
        model_exclude = ['id', 'instanceId', 'changeData', 'tasksType']


class ScheduledTaskSchemaOut(ModelSchema):
    class Config:
        model = ScheduledTasks
        model_fields = "__all__"


@router.post("/ScheduledTasks", response=ScheduledTaskSchemaOut)
def create_task(request, data: ScheduledTaskSchemaIn):
    tasks = create(request, data, ScheduledTasks)
    return tasks


api_url = "https://oapi.dingtalk.com/gettoken?appkey=%s&appsecret=%s" % (
'dingnauhobcjmoyuifbq', 'DFRp_ruRh-ntbJqhqe3yHK6-Y0tVfsLR7HgBLozqM5110t4JzUcALTSs_RpvKeEp')


def get_token():
    # try:
    res = requests.get(api_url)
    if res.status_code == 200:
        str_res = res.text
        token = (json.loads(str_res)).get('access_token')
        return token


def approveInstance(instanceId):
    # 所有部门信息
    url = 'https://api.dingtalk.com/v1.0/workflow/processInstances?processInstanceId=%s' % (instanceId)
    header = {
        "x-acs-dingtalk-access-token": get_token()
    }
    ret = json.loads(requests.get(url, header).text)
    res = ret.get('result').get('result')
    return res


# try:
#     scheduler = BackgroundScheduler()  # 创建定时任务的调度器对象——实例化调度器
#     # 调度器使用DjangoJobStore()
#     scheduler.add_jobstore(DjangoJobStore(), "default")
#
#     # 添加任务1
#     # 每隔5s执行这个任务
#     @register_job(scheduler, "interval", seconds=10, id='job1')
#     def job1():
#         # 具体要执行的代码
#         temp = ScheduledTasks.objects.all()
#         for i in temp:
#             obj = json.loads(i.changeData)
#             if approveInstance(i.instanceId) == "agree":
#                 print(obj)
#                 File.objects.filter(id=obj['id']).update(virtual_path='/'.join(obj['virtual_path']),
#                                                          permissions=','.join(obj['permissions']), name=obj['name'])
#                 ScheduledTasks.objects.get(id=i.id).delete()
#         print('任务运行成功！{}'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
#
#     # scheduler.add_job(job1, "interval", seconds=10, id="job2")
#
#     # 监控任务——注册定时任务
#     register_events(scheduler)
#     # 调度器开始运行
#     scheduler.start()
# except Exception as e:
#     print('定时任务异常：%s' % str(e))
