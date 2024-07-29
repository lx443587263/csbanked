# runapscheduler.py
import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from django_apscheduler.jobstores import DjangoJobStore
import time
import json
from django.shortcuts import get_object_or_404
from ninja import Field,ModelSchema

from system.apis.scheduled_tasks import approveInstance
from system.models import ScheduledTasks, File, Users
from system.apis.login import send_mail1


logger = logging.getLogger(__name__)

class SchemaIn(ModelSchema):
    dept_id: int = Field(None, alias="dept")
    post: list = []
    role: list = []

    class Config:
        model = Users
        model_exclude = ['id', 'groups', 'user_permissions', 'is_superuser', 'dept', 'post', 'role', 'password',
                         'create_datetime', 'update_datetime']

def my_job():
    # Your job processing logic here...
    # 具体要执行的代码
    temp = ScheduledTasks.objects.all()
    for i in temp:
        obj = json.loads(i.changeData)
        if approveInstance(i.instanceId) == "agree":
            if i.tasksType=="permissions":
                if obj['permissions']:
                    try:
                        File.objects.filter(id=obj['id']).update(virtual_path='/'.join(obj['virtual_path']),
                                                      permissions=','.join(obj['permissions']), name=obj['name'])
                    except:
                        File.objects.filter(id=obj['id']).update(permissions=','.join(obj['permissions']), name=obj['name'])
                    if 'adduser' in obj.keys():
                        for j in obj['adduser']:
                            send_mail1(
                                to_emails=Users.objects.filter(username=j)[0].email,
                                textMessage=r'''正和微芯的合作伙伴：

您好！

您有新的内容可以下载：
%s

        
顺颂商祺

珠海正和微芯科技有限公司
''' % (('/').join(obj['virtual_path'])),
                                subject='文件更新'
                                )
            elif i.tasksType == "account":
                if obj['role']:
                    get_object_or_404(Users, id=obj['id']).role.set(obj['role'])
                elif obj['post']:
                    get_object_or_404(Users, id=obj['id']).post.set(obj['role'])
                Users.objects.filter(id=obj['id']).update(
                    username=obj['username'],
                    name=obj['name'],
                    mobile=obj['mobile'],
                    email=obj['email'],
                    dept_id=obj['dept'],
                    home_path=obj['home_path'],
                    status=obj['status'],
                    avatar=obj['avatar'],
                    gender=obj['gender']
                )
            elif i.tasksType == "file":
                File.objects.filter(md5sum=obj['md5sum']).update(status=True)
            ScheduledTasks.objects.get(id=i.id).delete()
        elif approveInstance(i.instanceId) == "refuse":
            ScheduledTasks.objects.get(id=i.id).delete()
    print('任务运行成功！{}'.format(time.strftime("%Y-%m-%d %H:%M:%S")))



# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            my_job,
            trigger=CronTrigger(minute="*/1"),  # Every 10 seconds
            id="my_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")

