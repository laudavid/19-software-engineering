# login/views.py
import codecs
import csv

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages

from login import forms, models, tools
import re
import os
import nsfw_predict

from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

digit = re.compile("^\d{1,10}$")


class member:
    def __init__(self):
        self.name = ''
        self.history = 0


class choice:
    def __init__(self):
        self.content = ''
        self.choice_value = ''
        self.members = []


def index(request):
    return render(request, 'index.html')


def login(request):
    if request.session.get('is_login', None):
        messages.error(request, "请勿重复登录！")
        return redirect("/index/")

    if request.method == "POST":
        login_form = forms.LoginForm(request.POST)
        if not login_form.is_valid():
            messages.error(request, "表单信息有误！")
            render(request, 'login.html', locals())

        username = login_form.cleaned_data['username']
        password = login_form.cleaned_data['password']

        user = models.User.objects.filter(name=username).first()
        if not user:
            # Email login
            user = models.User.objects.filter(email=username).first()
            if not user:
                messages.error(request, "用户名未注册！")
                return render(request, 'login.html', locals())
            else:
                username = user.name
        if user.password != models.gen_md5(password, username):
            messages.error(request, "密码错误！")
            return render(request, 'login.html', locals())

        request.session['is_login'] = True
        # request.session['is_admin'] = user.is_admin
        request.session['is_admin'] = True
        request.session['username'] = username
        # messages.success(request, "登录成功！")
        request.session.set_expiry(3600)
        user.last_login_time = user.login_time
        user.login_time = timezone.now()
        user.save()
        return redirect('/all_task/')

    login_form = forms.LoginForm()
    return render(request, 'login.html', locals())


def register(request):
    if request.session.get('is_login', None):
        messages.error(request, "请先退出后再注册！")
        return redirect("/index/")

    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        if not register_form.is_valid():
            messages.error(request, "表单信息有误！")
            return render(request, 'regist.html', locals())

        username = register_form.cleaned_data['username']
        password1 = register_form.cleaned_data['password1']
        password2 = register_form.cleaned_data['password2']
        email = register_form.cleaned_data['email']

        if password1 != password2:  # 两次密码是否相同
            messages.error(request, "两次输入的密码不一致！")
            return render(request, 'regist.html', locals())
        if models.User.objects.filter(name=username).exists():  # 用户名是否唯一
            messages.error(request, "该用户名已注册！")
            return render(request, 'regist.html', locals())
        if models.User.objects.filter(email=email).exists():  # 邮箱地址是否唯一
            messages.error(request, "该邮箱已注册！")
            return render(request, 'regist.html', locals())

        new_user = models.User.objects.create()
        new_user.name = username
        new_user.password = models.gen_md5(password1, username)
        new_user.email = email
        new_user.is_admin = False  # 只能注册普通用户
        new_user.save()

        request.session['is_login'] = True  # 注册后自动登录
        # request.session['is_admin'] = user.is_admin
        request.session['is_admin'] = True
        request.session['username'] = username
        request.session.set_expiry(3600)
        messages.success(request, "注册成功！")
        new_user.last_login_time = new_user.login_time = timezone.now()
        new_user.save()
        return redirect('/index/')

    register_form = forms.RegisterForm()
    return render(request, 'regist.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        messages.error(request, "您尚未登录！")
        return redirect("/index/")

    request.session.flush()
    messages.success(request, "退出成功！")
    return redirect("/index/")


# 找回密码
def send(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not models.User.objects.filter(email=email).exists():
            messages.error(request, '邮箱未注册!')
            return render(request, 'FindPassword.html')
        else:
            # print(email)
            msg = '你收到这封邮件是因为你请求重置你在网站OneIsAll上的用户账户密码。请访问该页面并选择一个新密码：http://127.0.0.1:8000/ResetPassword/?email=' + email + '\n感谢使用我们的站点！\nOneIsAll团队'
            send_mail('密码重置邮件',
                      msg,
                      settings.EMAIL_FROM,
                      [email])
            return render(request, 'SendEmailDone.html')
    return render(request, 'FindPassword.html')


# 密码重置
def PwdReset(request):
    email = request.GET['email']
    if not email:
        messages.error(request, '无效的密码重置请求!')
    else:
        if request.method == 'POST':
            newPwd = request.POST.get('pwd')
            cPwd = request.POST.get('cpwd')
            if newPwd != cPwd:
                messages.error('两次输入不一致！')
                return render(request, 'PwdReset.html')
            else:
                user = models.User.objects.filter(email=email).first()
                user.password = models.gen_md5(newPwd, user.name)
                user.save()
                return render(request, 'PwdResetDone.html')
        return render(request, 'PwdReset.html')


def choose(request):
    if not request.session.get('is_admin', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    return render(request, 'choose.html', locals())


def release_task_1(request):
    if not request.session.get('is_admin', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    request.session['task_type'] = 1
    user = models.User.objects.get(name=request.session['username'])
    print("hhhhhh")
    return render(request, 'release_task.html', locals())


def release_task_2(request):
    if not request.session.get('is_admin', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    request.session['task_type'] = 2
    user = models.User.objects.get(name=request.session['username'])
    return render(request, 'release_task.html', locals())


def release_task_3(request):
    if not request.session.get('is_admin', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    request.session['task_type'] = 3
    user = models.User.objects.get(name=request.session['username'])
    return render(request, 'release_task_1.html', locals())


def release_task_4(request):
    if not request.session.get('is_admin', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    request.session['task_type'] = 4
    user = models.User.objects.get(name=request.session['username'])
    return render(request, 'release_task_2.html', locals())


def release_task(request):
    if not request.session.get('is_admin', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    if not request.session.get('task_type', None):
        return redirect("/choose/")

    if request.method == "POST":

        print(request.POST)
        # print(request.FILES)
        task_form = forms.TaskForm(request.POST, request.FILES)
        if not task_form.is_valid():
            print('sssssssssssssssssssssssssss')
            messages.error(request, "表单信息有误，请重新填写！")
            return release_task_x(request)

        files = request.FILES.getlist('files')  # exception
        # print(files)
        # print(type(files))

        template = task_form.cleaned_data['template']
        name = task_form.cleaned_data['name']
        details = task_form.cleaned_data['details']
        employees_num = task_form.cleaned_data['employees_num']
        # print('employees_num', employees_num, type(employees_num))
        credit = task_form.cleaned_data['credit']
        user_level = task_form.cleaned_data['user_level']
        current_user = models.User.objects.get(name=request.session['username'])
        if current_user.total_credits < credit * employees_num * len(files):
            messages.error(request, "您的信用积分不足，请先进行充值！")
            return recharge(request)

        new_task = models.Task.objects.create()
        new_task.type = request.session['task_type']
        new_task.name = name
        new_task.admin = current_user
        new_task.template = int(template)
        new_task.details = details
        new_task.max_tagged_num = employees_num
        new_task.credit = credit
        new_task.user_level = user_level
        # save questions and answers
        i = 1
        content = ''
        while 'q' + str(i) in request.POST:
            question = request.POST.get('q' + str(i))
            if len(question) <= 0 or len(question) > 128:
                messages.error(request, "表单信息有误，请重新填写！")
                return release_task_x(request)
            content += '|' + question
            j = 1
            while 'a' + str(j) + '_q' + str(i) in request.POST:
                choice = request.POST.get('a' + str(j) + '_q' + str(i))
                if len(choice) <= 0 or len(choice) > 128:
                    messages.error(request, "表单信息有误，请重新填写！")
                    return release_task_x(request)
                content += '&' + choice
                j += 1
            i += 1
        new_task.content = content
        new_task.save()

        i = 1
        while 'm' + str(i) in request.POST:
            member = request.POST.get('m' + str(i))
            if not models.User.objects.filter(name=member).exists():
                messages.error(request, member + "用户不存在")
            else:
                u = models.User.objects.filter(name=member).first()
                u.tasks_to_examine.add(new_task)
                u.save()
            i += 1

        # save images
        for f in files:
            sub_task = models.SubTask.objects.create()
            sub_task.file = f
            sub_task.task = new_task
            sub_task.save()

        imagelist = os.listdir('./media/task_' + str(new_task.id))
        illegallist = []
        for f in imagelist:
            legal = nsfw_predict.predict(f, 'media/task_' + str(new_task.id))
            if (legal == 1):
                illegallist.append('../media/task_' + str(new_task.id) + '/' + str(f))
        # print('../media/task_' + str(new_task.id)+'/'+str(f))
        if (legal == 1):
            return render(request, 'check_pic.html', locals())

        current_user.total_credits -= credit * employees_num * len(files)
        current_user.save()

        del request.session['task_type']
        request.session['new_task_id'] = new_task.id
        if new_task.template == 1:
            return redirect('/confirm_to_upload_pictures/')
        elif new_task.template == 2 and new_task.type == 4:
            return redirect('/video2pictures_slide/')
        else:
            del request.session['new_task_id']
            messages.success(request, "任务发布成功！")
            return redirect('/all_task/')

    return release_task_x(request)


def release_task_x(request):
    if request.session['task_type'] == 1:
        return redirect('/release_task_1/')
    elif request.session['task_type'] == 2:
        return redirect('/release_task_2/')
    elif request.session['task_type'] == 3:
        return redirect('/release_task_3/')
    elif request.session['task_type'] == 4:
        return redirect('/release_task_4/')
    return redirect('/all_task/')


def video2pictures_slide(request):
    if not request.session.get('is_admin', None) or not request.session.get('new_task_id', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    task_id = request.session['new_task_id']
    task = models.Task.objects.filter(pk=task_id).first()
    if not task or task.type != 4 or task.template != 2:
        messages.error(request, '页面已过期！')
        return redirect("/all_task/")

    if request.method == "POST":
        # print(request.POST)
        if 'frame' in request.POST and 'frame_interval' in request.POST:
            if not digit.match(request.POST.get('frame_interval')):
                messages.error(request, "请输入合法的帧数间隔！")
            else:
                frame_interval = int(request.POST.get('frame_interval'))
                tools.video2pictures(task, frame_interval)
                request.session['frame'] = frame_interval
        elif 'confirm' in request.POST:
            if not request.session.get('frame', None):
                messages.error(request, "请先输入合法的帧数间隔！")
            else:
                del request.session['new_task_id']
                del request.session['frame']
                messages.success(request, "任务发布成功！")
                return redirect("/all_task/")
        elif 'return' in request.POST:
            current_user = models.User.objects.get(name=request.session['username'])
            current_user.released_tasks.filter(pk=task_id).delete()
            del request.session['new_task_id']
            del request.session['frame']
            return redirect("/all_task/")
        elif 'abandon' in request.POST and digit.match(request.POST.get('abandon')):
            screenshot = models.Screenshot.objects.filter(id=int(request.POST.get('abandon'))).first()
            if screenshot and screenshot.sub_task.task.id == task_id:
                screenshot.delete()

    return render(request, 'video2pictures_slide.html', locals())


def confirm_to_upload_pictures(request):
    if not request.session.get('is_admin', None) or not request.session.get('new_task_id', None):
        messages.error(request, "页面已过期！")
        return redirect("/all_task/")
    task_id = request.session['new_task_id']
    task = models.Task.objects.filter(pk=task_id).first()
    if not task or task.template != 1:
        messages.error(request, '页面已过期！')
        return redirect("/all_task/")

    if request.method == "POST":
        # print(request.POST)
        if 'abandon' in request.POST and digit.match(request.POST.get('abandon')):
            sub_task_id = int(request.POST.get('abandon'))
            task.subtask_set.filter(pk=sub_task_id).delete()
            current_user = models.User.objects.get(name=request.session['username'])
            current_user.total_credits += task.credit * task.max_tagged_num
            current_user.save()
        elif 'confirm' in request.POST:
            del request.session['new_task_id']
            messages.success(request, "任务发布成功！")
            return redirect("/all_task/")

    sub_tasks = task.subtask_set.all()
    return render(request, 'confirm_to_upload_pictures.html', locals())


def all_task(request):
    task_list = models.Task.objects.all()
    num_task = task_list.count()
    num_user = models.User.objects.count()
    task_templates = ['', '图片', '视频', '音频']
    task_types = ['', '单选式', '多选式', '问答式', '标注式']
    temp_excluded_list = []
    if request.method == "POST":
        # print(request.POST)
        if 'task_sort' in request.POST or 'task_filter' in request.POST or 'task_value' in request.POST or 'task_keyword' in request.POST:
            temp_excluded_list = request.POST.getlist('temp_excluded')
            if 'temp1' in temp_excluded_list:
                task_list = task_list.exclude(template=1, type=1).exclude(template=1, type=2)
            if 'temp2' in temp_excluded_list:
                task_list = task_list.exclude(template=1, type=3)
            if 'temp3' in temp_excluded_list:
                task_list = task_list.exclude(template=1, type=4)
            if 'temp4' in temp_excluded_list:
                task_list = task_list.exclude(template=3, type=1).exclude(template=3, type=2)
            if 'temp5' in temp_excluded_list:
                task_list = task_list.exclude(template=3, type=3)
            if 'temp6' in temp_excluded_list:
                task_list = task_list.exclude(template=2, type=1).exclude(template=2, type=2)
            if 'temp7' in temp_excluded_list:
                task_list = task_list.exclude(template=2, type=3)
            if 'temp8' in temp_excluded_list:
                task_list = task_list.exclude(template=2, type=4)
            # print(task_list)
            if request.POST.get('tagged_num') == 'single':
                task_list = task_list.filter(max_tagged_num=1)
            elif request.POST.get('tagged_num') == 'multi':
                task_list = task_list.exclude(max_tagged_num=1)
            if request.POST.get('order') == 'time_desc':
                task_list = task_list.order_by('-c_time')
            elif request.POST.get('order') == 'num_asc':
                task_list = task_list.order_by('max_tagged_num')
            elif request.POST.get('order') == 'num_desc':
                task_list = task_list.order_by('-max_tagged_num')
            # 筛选任务积分高于某值的任务
            if request.POST.get('value') != '':
                print("value:" + request.POST.get('value'))
                if not request.POST.get('value').isdigit():
                    messages.error(request, "value 中包含非数字")
                else:
                    task_list = task_list.filter(credit__gt=request.POST.get('value')).order_by('-credit')
            # 任务关键词筛选
            if request.POST.get('KeyWord') != '':
                print("Key:" + request.POST.get('KeyWord'))
                task_list = task_list.filter(name__contains=request.POST.get('KeyWord'))

    if not request.session.get('is_login', None):
        return render(request, 'all_task.html', locals())

    current_user = models.User.objects.get(name=request.session['username'])
    rank = models.User.objects.filter(num_label_accepted__gt=current_user.num_label_accepted).count() + 1

    if request.method == "POST":
        # print(request.POST)
        if 'collect' in request.POST:
            collect_task(request, current_user)
        elif 'remove' in request.POST:
            remove_task(request, current_user)
        elif 'enter' in request.POST:
            if digit.match(request.POST.get('enter')):
                request.session['task_id'] = int(request.POST.get('enter'))
                return redirect('/enter_task/')
        elif 'cancel_tasks' in request.POST:
            cancel_task(request)
            task_list = models.Task.objects.all()
            num_task = task_list.count()
        elif 'review' in request.POST and digit.match(request.POST.get('review')):
            request.session['task_id'] = int(request.POST.get('review'))
            return redirect('/one_task/')
        elif 'close_task' in request.POST and digit.match(request.POST.get('close_task')):
            task_id = int(request.POST.get('close_task'))
            task = current_user.released_tasks.filter(id=task_id).first()
            if task:
                task.is_closed = True
                task.save()

        elif 'redo_unreviewed_task' in request.POST and digit.match(request.POST.get('redo_unreviewed_task')):
            request.session['task_id'] = int(request.POST.get('redo_unreviewed_task'))
            task_user = models.TaskUser.objects.filter(task_id=request.session['task_id'],
                                                       user=current_user, status='unreviewed').first()
            if not task_user:
                return redirect('/enter_task/')
            task_user.status = 'doing'
            task_user.label_set.filter(status='unreviewed').update(status='untagged')
            task_user.save()
            return redirect('/enter_task/')
        elif 'abandon_unreviewed_task' in request.POST and digit.match(request.POST.get('abandon_unreviewed_task')):
            task_id = int(request.POST.get('abandon_unreviewed_task'))
            task_user = models.TaskUser.objects.filter(Q(status='doing') | Q(status='unreviewed'), task_id=task_id,
                                                       user=current_user).first()
            if not task_user:
                return redirect('/enter_task/')
            task_user.status = 'abandoned'
            task_user.label_set.filter(status='unreviewed').update(status='untagged')
            task_user.task.num_worker -= 1
            task_user.task.save()
            task_user.save()
        elif 'redo_rejected_task' in request.POST and digit.match(request.POST.get('redo_rejected_task')):
            request.session['task_id'] = int(request.POST.get('redo_rejected_task'))
            task_user = models.TaskUser.objects.filter(task_id=request.session['task_id'],
                                                       user=current_user, status='rejected').first()
            if not task_user:
                return redirect('/enter_task/')
            rejected_labels = task_user.label_set.filter(status='rejected')
            task_user.num_label_unreviewed += rejected_labels.count()
            task_user.num_label_rejected = 0
            task_user.status = 'redoing'
            task_user.save()
            rejected_labels.update(status='untagged')
            return redirect('/enter_task/')

        elif 'abandon_rejected_task' in request.POST and digit.match(request.POST.get('abandon_rejected_task')):
            task_id = int(request.POST.get('abandon_rejected_task'))
            task_user = models.TaskUser.objects.filter(Q(status='rejected') | Q(status='redoing'), task_id=task_id,
                                                       user=current_user).first()
            if not task_user:
                return redirect('/enter_task/')
            rejected_labels = task_user.label_set.filter(status='rejected')
            task_user.num_label_unreviewed += rejected_labels.count()
            task_user.num_label_rejected = 0
            task_user.status = 'abandoned'
            task_user.task.num_worker -= 1
            task_user.task.save()
            task_user.save()
            rejected_labels.update(status='untagged')

        elif 'take_a_position' in request.POST and digit.match(request.POST.get('take_a_position')):
            task_id = int(request.POST.get('take_a_position'))
            grab_task(request, current_user, task_id)

    favorite_task_list = current_user.favorite_tasks.all()
    num_favorite_task = favorite_task_list.count()

    released_task_list = current_user.released_tasks.all()
    num_released_task = released_task_list.count()

    rejected_task_list = current_user.claimed_tasks.filter(
        Q(taskuser__status='rejected') | Q(taskuser__status='redoing'), taskuser__user=current_user).distinct()
    num_rejected_task = rejected_task_list.count()

    unreviewed_task_list = current_user.claimed_tasks.filter(taskuser__status='unreviewed',
                                                             taskuser__user=current_user).distinct()
    num_unreviewed_task = unreviewed_task_list.count()

    get_position_task_list = current_user.claimed_tasks.filter(taskuser__status='doing', taskuser__has_grabbed=True,
                                                               taskuser__user=current_user).distinct()

    # 审核组后台数据获取
    Tasks_to_examine = current_user.tasks_to_examine.filter(taskuser__num_label_unreviewed__gt=0).distinct()
    num_tasks_to_examine = Tasks_to_examine.count()

    current_user.login_time = timezone.now()
    current_user.save()
    num_updated_task = models.Task.objects.filter(c_time__gt=current_user.last_login_time).count()
    label_accepted_new = current_user.label_set.filter(status='accepted',
                                                       m_time__gt=current_user.last_login_time)
    num_label_accepted_new = label_accepted_new.count()
    credits_new = 0
    for label in label_accepted_new:
        credits_new += label.sub_task.task.credit
    return render(request, 'all_task.html', locals())


def grab_task(request, current_user, task_id):
    task = models.Task.objects.filter(id=task_id).first()
    if not task:
        messages.error(request, '任务不存在！')
        return

    level_list = [0, 0, 200, 500, 1000, 2000]
    if current_user.num_label_accepted < level_list[task.user_level]:
        messages.error(request, '您的等级不足，无法抢该任务！')
        return
    if task.is_closed:
        messages.error(request, '该任务已关闭！')
        return

    if task.num_worker < task.max_tagged_num:
        messages.error(request, '该任务未满员，可直接进入！')
        return

    task_user = models.TaskUser.objects.filter(task=task, user=current_user).first()
    if task_user:
        if task_user.status == 'doing' or task_user.status == 'redoing':
            messages.error(request, '您可以直接进入该任务！')
            return
        elif task_user.status == 'grabbing':
            messages.success(request, '已为您预约抢位！')
            return
        else:
            messages.error(request, '您已经做过该任务！')
            return

    task_user = models.TaskUser.objects.filter(task_id=task_id, status='rejected').first()
    if task_user:
        task_user.status = 'grabbed'
        task_user.save()
        rejected_labels = task_user.label_set.filter(status='rejected')
        new_task_user = models.TaskUser.objects.create(task=task, user=current_user, status='doing', has_grabbed=True,
                                                       num_label_unreviewed=rejected_labels.count())
        rejected_labels.update(user=current_user, task_user=new_task_user, status='untagged')
        messages.success(request, '抢位成功！')
    else:
        models.TaskUser.objects.create(task=task, user=current_user, status='grabbing')
        messages.success(request, '已为您预约抢位！')


def collect_task(request, current_user):
    if not request.session.get('is_login', None) or not digit.match(request.POST.get('collect')):
        messages.error(request, '用户未登录！')
        return
    task_id = int(request.POST.get('collect'))
    task = models.Task.objects.filter(pk=task_id).first()
    if not task:
        messages.error(request, '该任务不存在！')
        return
    current_user.favorite_tasks.add(task)


def remove_task(request, current_user):
    if not request.session.get('is_login', None):
        messages.error(request, '用户未登录！')
        return
    task_id_list = request.POST.getlist('removed_task_id_list')
    for task_id in task_id_list:
        if not digit.match(task_id):
            continue
        task = current_user.favorite_tasks.filter(id=task_id).first()
        if task:
            current_user.favorite_tasks.remove(task)


def cancel_task(request):
    if not request.session.get('is_admin', None):
        return
    current_user = models.User.objects.get(name=request.session['username'])
    task_id_list = request.POST.getlist('canceled_task_id_list')
    for task_id in task_id_list:
        if not digit.match(task_id):
            # print('该task_id不合法！')
            continue
        task_id = int(task_id)
        task = current_user.released_tasks.filter(pk=task_id).first()
        if task:
            task.is_closed = True
            task.save()
        # task = current_user.released_tasks.filter(pk=task_id).first()
        # if not task:
        #     print('该任务不存在！')
        #     continue
        # task.delete()
        # task.is_closed = True
        # task.save()


def enter_task(request):
    if not request.session.get('is_login', None) or not request.session.get('task_id', None):
        messages.error(request, '用户未登录！')
        return redirect('/all_task/')
    current_user = models.User.objects.get(name=request.session['username'])
    task = models.Task.objects.filter(id=request.session['task_id']).first()
    if not task:
        messages.error(request, '任务不存在！')
        return redirect('/all_task/')

    level_list = [0, 0, 200, 500, 1000, 2000]
    if task.is_closed:
        messages.error(request, '该任务已关闭！')
        return redirect('/all_task/')
    if current_user.num_label_accepted < level_list[task.user_level]:
        messages.error(request, '您的等级不足，无法进入该任务！')
        return redirect('/all_task/')

    task_user = models.TaskUser.objects.filter(task=task, user=current_user).first()
    if not task_user:
        if task.num_worker >= task.max_tagged_num:
            messages.error(request, '该任务已满员，无法进入！')
            return redirect('/all_task/')
        task_user = models.TaskUser.objects.create(task=task, user=current_user)
        task.num_worker += 1
        task.save()
        abandoned_task_user = task.taskuser_set.filter(status='abandoned').first()
        if abandoned_task_user:
            abandoned_labels = abandoned_task_user.label_set.filter(status='untagged')
            task_user.num_label_unreviewed = abandoned_labels.count()
            task_user.save()
            abandoned_task_user.status = 'gotten'
            abandoned_task_user.save()
            abandoned_labels.update(task_user=task_user, user=current_user)
        else:
            sub_task_set = task.subtask_set.all()
            task_user.num_label_unreviewed = sub_task_set.count()
            task_user.save()
            for sub_task in sub_task_set:
                models.Label.objects.create(sub_task=sub_task, task_user=task_user, user=current_user)
    if task_user.status != 'doing' and task_user.status != 'redoing':
        if task_user.status == 'grabbing':
            messages.error(request, '已为您预约抢位！')
            return redirect('/all_task/')
        else:
            messages.error(request, '您已经做过该任务！')
            return redirect('/all_task/')

    # task_templates = ['', '图片', '视频', '音频']
    # task_types = ['', '单选式', '多选式', '问答式', '标注式']
    if task.template == 1:
        return picture_task(request, current_user, task, task_user)
    elif task.template == 2:
        return video_task(request, current_user, task, task_user)
    elif task.template == 3:
        return player_task(request, current_user, task, task_user)
    return redirect('/all_task/')


def picture_task(request, current_user, task, task_user):
    if request.method == "POST":
        # print(request.POST)
        result = ''
        if task.type != 4:
            i = 1
            while 'q' + str(i) in request.POST:
                result += '|' + 'q' + str(i)
                answers = request.POST.getlist('q' + str(i))
                # print(answers)
                for answer in answers:
                    result += '&' + answer
                i += 1
        else:
            result = request.POST.get('position').replace('\r\n', '|')

        label_id = request.session.get('label_id', None)
        if result == '' and task.type == 2:
            messages.error(request, '请至少选择一项结果！')
        elif label_id:
            label = models.Label.objects.get(pk=label_id)
            print(label.sub_task)
            label.status = 'unreviewed'
            label.result = result
            label.save()
            if task.type == 4:
                tools.picture_circle(label)
            del request.session['label_id']

    label = task_user.label_set.filter(status='untagged').first()
    if not label:
        messages.success(request, "该任务已完成！")
        task_user.status = 'unreviewed'
        task_user.save()
        del request.session['task_id']
        return redirect('/all_task/')
    request.session['label_id'] = label.id
    sub_task = label.sub_task

    qa_list = []
    contents = task.content.split('|')
    for item in contents[1:]:
        qa = item.split('&')
        qa_list.append({'question': qa[0], 'answers': qa[1:]})

    if task.type == 1:
        return render(request, 'picture_task.html', locals())
    elif task.type == 2:
        return render(request, 'picture_task_multi_choice.html', locals())
    elif task.type == 3:
        return render(request, 'picture_task_qa.html', locals())
    else:
        return render(request, 'picture_circle.html', locals())


def video_task(request, current_user, task, task_user):
    if request.method == "POST":
        # print(request.POST)
        result = ''
        if task.type != 4:
            i = 1
            while 'q' + str(i) in request.POST:
                result += '|' + 'q' + str(i)
                answers = request.POST.getlist('q' + str(i))
                # print(answers)
                for answer in answers:
                    result += '&' + answer
                i += 1
        else:
            result = request.POST.get('position').replace('\r\n', '|')

        label_id = request.session.get('label_id', None)
        if result == '' and task.type == 2:
            messages.error(request, '请至少选择一项结果！')
        elif label_id:
            label = models.Label.objects.get(pk=label_id)
            print(label.sub_task)
            label.status = 'unreviewed'
            label.result = result
            label.save()
            if task.type == 4:
                tools.video_circle(label)
            del request.session['label_id']

    label = task_user.label_set.filter(status='untagged').first()
    if not label:
        messages.success(request, "该任务已完成！")
        task_user.status = 'unreviewed'
        task_user.save()
        del request.session['task_id']
        return redirect('/all_task/')
    request.session['label_id'] = label.id
    sub_task = label.sub_task

    qa_list = []
    contents = task.content.split('|')
    for item in contents[1:]:
        qa = item.split('&')
        qa_list.append({'question': qa[0], 'answers': qa[1:]})

    if task.type == 1:
        return render(request, 'video_task.html', locals())
    elif task.type == 2:
        return render(request, 'video_task_multi_choice.html', locals())
    elif task.type == 3:
        return render(request, 'video_task_qa.html', locals())
    else:
        img_name_list = ''
        for screen_shot in sub_task.screenshot_set.all():
            img_name_list += '#' + screen_shot.image.name.split('\\')[-1]
        return render(request, 'video_circle.html', locals())


def player_task(request, current_user, task, task_user):
    if request.method == "POST":
        # print(request.POST)
        i = 1
        result = ''
        while 'q' + str(i) in request.POST:
            result += '|' + 'q' + str(i)
            answers = request.POST.getlist('q' + str(i))
            # print(answers)
            for answer in answers:
                result += '&' + answer
            i += 1

        label_id = request.session.get('label_id', None)
        if result == '' and task.type == 2:
            messages.error(request, '请至少选择一项结果！')
        elif label_id:
            label = models.Label.objects.get(pk=label_id)
            print(label.sub_task)
            label.status = 'unreviewed'
            label.result = result
            label.save()
            if task.type == 4:
                tools.video_circle(label)
            del request.session['label_id']

    label = task_user.label_set.filter(status='untagged').first()
    if not label:
        messages.success(request, "该任务已完成！")
        task_user.status = 'unreviewed'
        task_user.save()
        del request.session['task_id']
        return redirect('/all_task/')
    request.session['label_id'] = label.id
    sub_task = label.sub_task

    qa_list = []
    contents = task.content.split('|')
    for item in contents[1:]:
        qa = item.split('&')
        qa_list.append({'question': qa[0], 'answers': qa[1:]})

    if task.type == 1:
        return render(request, 'player_task.html', locals())
    elif task.type == 2:
        return render(request, 'player_task_multi_choice.html', locals())
    else:
        return render(request, 'player_task_qa.html', locals())


def reject_label(label, task):
    label.status = 'rejected'
    task_user = label.task_user
    task_user.num_label_unreviewed -= 1
    task_user.num_label_rejected += 1
    if task_user.num_label_unreviewed == 0:
        new_task_user = task.taskuser_set.filter(status='grabbing').first()
        if new_task_user:
            rejected_labels = task_user.label_set.filter(status='rejected')
            rejected_labels.update(user=new_task_user.user, task_user=new_task_user, status='untagged')
            new_task_user.status = 'doing'
            new_task_user.has_grabbed = True
            new_task_user.num_label_unreviewed = rejected_labels.count()
            new_task_user.save()
            task_user.status = 'grabbed'
        else:
            task_user.status = 'rejected'
    task_user.save()
    label.save()


def accept_label(label, task):
    label.status = 'accepted'
    label.user.total_credits += label.sub_task.task.credit
    label.user.num_label_accepted += 1
    label.user.save()
    task_user = label.task_user
    task_user.num_label_unreviewed -= 1
    if task_user.num_label_unreviewed == 0:
        if task_user.num_label_rejected > 0:
            new_task_user = task.taskuser_set.filter(status='grabbing').first()
            if new_task_user:
                rejected_labels = task_user.label_set.filter(status='rejected')
                rejected_labels.update(user=new_task_user.user, task_user=new_task_user, status='untagged')
                new_task_user.status = 'doing'
                new_task_user.has_grabbed = True
                new_task_user.num_label_unreviewed = rejected_labels.count()
                new_task_user.save()
                task_user.status = 'grabbed'
            else:
                task_user.status = 'rejected'
        else:
            task_user.status = 'accepted'
    task_user.save()
    label.save()


def check_task(request):
    if not request.session.get('is_admin', None) or not request.session.get('task_id', None) or not request.session.get(
            'sub_task_id', None):
        return redirect('/all_task/')
    current_user = models.User.objects.get(name=request.session['username'])
    task = current_user.released_tasks.filter(id=request.session['task_id']).first()
    if not task:
        return redirect('/all_task/')
    sub_task = task.subtask_set.filter(id=request.session['sub_task_id']).first()
    if not sub_task:
        return redirect('/all_task/')

    if request.method == "POST":
        # print(request.POST)
        if 'pass' in request.POST:
            if not digit.match(request.POST.get('pass')):
                messages.error(request, '该label_id不合法！')
                return redirect('/all_task/')
            label = sub_task.label_set.filter(pk=request.POST.get('pass')).first()
            if not label:
                messages.error(request, '该标签不存在！')
                return redirect('/all_task/')
            accept_label(label, task)
        elif 'back' in request.POST:
            if not digit.match(request.POST.get('back')):
                messages.error(request, '该label_id不合法！')
                return redirect('/all_task/')
            label = sub_task.label_set.filter(pk=request.POST.get('back')).first()
            if not label:
                messages.error(request, '该标签不存在！')
                return redirect('/all_task/')
            reject_label(label, task)
        elif 'detail' in request.POST and task.type == 4:
            request.session['label_id'] = int(request.POST.get('detail'))
            return redirect('/picture_detail/')
        elif 'pass_all' in request.POST:
            label_list = sub_task.label_set.filter(status='unreviewed')
            for label in label_list:
                accept_label(label, task)

    label_list = sub_task.label_set.exclude(status='untagged')
    # print(label_list)
    qa_list = []
    contents = task.content.split('|')

    if task.type == 1 or task.type == 2:
        for i, item in enumerate(contents[1:]):
            qa = item.split('&')
            answers = []
            for ans in qa[1:]:
                answers.append([ans, 0])
            for label in label_list:
                ans_list = label.result.split('|')[i + 1].split('&')[1:]
                for ans in ans_list:
                    answers[int(ans) - 1][1] += 1
            qa_list.append({'question': qa[0], 'answers': answers})
        return render(request, 'choice_questions_result.html', locals())
    elif task.type == 3:
        return render(request, 'qa_result.html', locals())
    else:
        return render(request, 'picture_result.html', locals())


def picture_detail(request):
    if not request.session.get('is_admin', None) or \
            not request.session.get('task_id', None) or \
            not request.session.get('sub_task_id', None) or \
            not request.session.get('label_id', None):
        return redirect('/all_task/')

    current_user = models.User.objects.get(name=request.session['username'])
    task = current_user.released_tasks.filter(id=request.session['task_id']).first()
    if not task:
        return redirect('/all_task/')
    sub_task = task.subtask_set.filter(id=request.session['sub_task_id']).first()
    if not sub_task:
        return redirect('/all_task/')
    label = sub_task.label_set.filter(id=request.session['label_id']).first()
    if not label:
        return redirect('/all_task/')

    if request.method == "POST":
        print(request.POST)
        if 'pass' in request.POST:
            if not digit.match(request.POST.get('pass')):
                messages.error(request, '该label_id不合法！')
                return redirect('/all_task/')
            label = sub_task.label_set.filter(pk=request.POST.get('pass')).first()
            if not label:
                messages.error(request, '该标签不存在！')
                return redirect('/all_task/')
            accept_label(label, task)
        elif 'back' in request.POST:
            if not digit.match(request.POST.get('back')):
                messages.error(request, '该label_id不合法！')
                return redirect('/all_task/')
            label = sub_task.label_set.filter(pk=request.POST.get('back')).first()
            if not label:
                messages.error(request, '该标签不存在！')
                return redirect('/all_task/')
            reject_label(label, task)

    contents = task.content.split('|')
    return render(request, 'picture_detail.html', locals())


def one_task(request):
    if not request.session.get('is_admin', None) or not request.session.get('task_id', None):
        return redirect('/all_task/')
    current_user = models.User.objects.get(name=request.session['username'])
    task = current_user.released_tasks.filter(id=request.session['task_id']).first()
    if not task:
        return redirect('/all_task/')

    if request.method == "POST":
        if 'enter' in request.POST and digit.match(request.POST.get('enter')):
            request.session['sub_task_id'] = int(request.POST.get('enter'))  # need some check
            return redirect('/check_task/')
    rank = models.User.objects.filter(num_label_accepted__gt=current_user.num_label_accepted).count() + 1
    sub_task_list = task.subtask_set.all()
    num_favorite_task = current_user.favorite_tasks.count()
    num_released_task = current_user.released_tasks.count()

    rejected_task_list = current_user.claimed_tasks.filter(
        Q(taskuser__status='rejected') | Q(taskuser__status='redoing'), taskuser__user=current_user).distinct()
    num_rejected_task = rejected_task_list.count()

    unreviewed_task_list = current_user.claimed_tasks.filter(taskuser__status='unreviewed',
                                                             taskuser__user=current_user).distinct()
    num_unreviewed_task = unreviewed_task_list.count()

    num_updated_task = models.Task.objects.filter(c_time__gt=current_user.last_login_time).count()
    label_accepted_new = current_user.label_set.filter(status='accepted',
                                                       m_time__gt=current_user.last_login_time)
    num_label_accepted_new = label_accepted_new.count()
    credits_new = 0
    for label in label_accepted_new:
        credits_new += label.sub_task.task.credit
    return render(request, 'one_task.html', locals())


def recharge(request):
    if not request.session.get('is_login', None):
        return redirect('/all_task/')
    current_user = models.User.objects.get(name=request.session['username'])

    if request.method == "POST" and 'docVlGender' in request.POST:
        # print(request.POST)
        if request.POST.get('docVlGender') == '10':
            current_user.total_credits += 10
            current_user.save()
        elif request.POST.get('docVlGender') == '20':
            current_user.total_credits += 20
            current_user.save()
        elif request.POST.get('docVlGender') == '50':
            current_user.total_credits += 50
            current_user.save()
        elif request.POST.get('docVlGender') == 'other' and 'other_amount' in request.POST and digit.match(
                request.POST.get('other_amount')):
            current_user.total_credits += int(request.POST.get('other_amount'))
            current_user.save()
        else:
            messages.error(request, "充值失败！")
            return render(request, 'recharge.html', locals())
        messages.success(request, "充值成功！")
        if request.session.get('task_type'):
            return release_task_x(request)
        else:
            return redirect('/all_task/')
    return render(request, 'recharge.html', locals())


def download_data_set(request):
    if not request.session.get('is_admin', None) or not request.session.get('task_id', None) or not request.session.get(
            'sub_task_id', None):
        return redirect('/all_task/')
    # current_user = models.User.objects.get(name=request.session['username'])
    task = models.Task.objects.get(id=request.session['task_id'])
    sub_task = models.SubTask.objects.get(id=request.session['sub_task_id'])

    response = HttpResponse(content_type='text/csv')
    response.write(codecs.BOM_UTF8)
    response['Content-Disposition'] = 'attachment; filename="task_{}_sub_task_{}.csv"'.format(task.id, sub_task.id)

    writer = csv.writer(response)
    label_list = sub_task.label_set.filter()
    # print(label_list)
    contents = task.content.split('|')

    if task.type == 4:
        writer.writerow(['User', 'Picture', 'Position', 'Type'])
        label = models.Label.objects.filter(id=request.session['label_id']).first()
        for result in label.result.split('|')[:-1]:
            results = result.split(' & ')
            answer_list = [label.user.name, results[0], results[1], contents[int(results[-1])]]
            writer.writerow(answer_list)
            # print(answer_list)
        return response

    question_list = ['User']
    for i, content in enumerate(contents[1:]):
        question_list.append('Q{}:{}'.format(i + 1, content.split('&')[0]))
    writer.writerow(question_list)
    # print(question_list)
    for label in label_list:
        answer_list = [label.user.name]

        for i, content in enumerate(label.result.split('|')[1:]):
            answer = ''
            if task.type == 1 or task.type == 2:
                answers = content.split('&')[1:]
                for ans in answers:
                    answer += '{}.{};'.format(chr(64 + int(ans)), contents[i + 1].split('&')[int(ans)])
            elif task.type == 3:
                answer = content.split('&')[-1]
            answer_list.append(answer)

        writer.writerow(answer_list)
        # print(answer_list)
    return response


def check_pic(request):
    return render(request, 'check_pic.html', locals())


def choice_questions_result(request):
    print(request.POST)
    if not request.session.get('task_id', None) or not request.session.get('sub_task_id', None):
        return redirect('/all_task/')
    task = models.Task.objects.filter(id=request.session['task_id']).first()
    if not task:
        return redirect('/all_task/')
    sub_task = task.subtask_set.filter(id=request.session['sub_task_id']).first()
    if not sub_task:
        return redirect('/all_task/')

    label_list = sub_task.label_set.exclude(status='untagged')
    # print(label_list)
    qa_list = []
    contents = task.content.split('|')
    sum = len(label_list)
    choice_list = []

    for i, item in enumerate(contents[1:]):
        qa = item.split('&')
        answers = []
        for ans in qa[1:]:
            answers.append([ans, 0, []])
        for label in label_list:
            ans_list = label.result.split('|')[i + 1].split('&')[1:]
            for ans in ans_list:
                answers[int(ans) - 1][1] += 1
                answers[int(ans) - 1][2].append((label.user.name, label.user.num_label_accepted))
        qa_list.append({'question': qa[0], 'answers': answers})

    if request.method == 'POST':
        qa_num = len(qa_list)
        for i in range(1, qa_num + 1):
            if 'q' + str(i) in request.POST:
                index = int(request.POST.get('q' + str(i)))

        c_list = qa_list[index - 1]
        a_list = c_list['answers']
        i = 1
        for item in a_list:
            c = choice()
            c.content += chr(64 + i) + '.'
            c.content += item[0]
            c.choice_value = "%.1f%%" % (item[1] / sum * 100)
            for unit in item[2]:
                m = member()
                m.name = unit[0]
                m.history = unit[1]
                c.members.append(m)
            choice_list.append(c)
            i += 1
        request.session['answers_data'] = (a_list, sum, task.type)
        return render(request, 'chart.html', locals())


def getIntersection(uinList):
    while len(uinList) > 1:
        list_a = []
        list_b = []
        list_a = uinList.pop()
        list_b = uinList.pop()
        list_c = list(set(list_a).intersection(set(list_b)))
        if len(list_c) > 0:
            uinList.append(list_c)
    return uinList[0]


def chart(request):
    if not request.session.get('task_id', None) or not request.session.get('sub_task_id',
                                                                           None) or not request.session.get(
            'answers_data', None):
        return redirect('/all_task/')
    task = models.Task.objects.filter(id=request.session['task_id']).first()
    if not task:
        return redirect('/all_task/')
    sub_task = task.subtask_set.filter(id=request.session['sub_task_id']).first()
    if not sub_task:
        return redirect('/all_task/')

    if request.method == 'POST':
        print(request.POST)
        threshold = int(request.POST.get('value_'))
        info = request.session['answers_data']
        sum = info[1]
        if info[2] == 1:
            a_list = info[0]
            for item in a_list:
                if item[1] / sum * 100 > threshold:
                    for member in item[2]:
                        m = models.User.objects.get(name=member[0])
                        label = sub_task.label_set.filter(user=m).first()
                        # Pass
                        accept_label(label, label.sub_task.task)
        if info[2] == 2:
            a_list = info[0]
            choices_mem_list = []
            mem_list = []
            final = []
            for item in a_list:
                if item[1] / sum * 100 > threshold:
                    choices_mem_list.append(item[2])
                    a_list.remove(item)
            mem_list = getIntersection(choices_mem_list)
            for mem in mem_list:
                flag = 0
                for item in a_list:
                    if mem in item[2]:
                        flag = 1
                        break
                if flag == 0:
                    final.append(mem)
            for mem in final:
                m = models.User.objects.get(name=mem[0])
                label = sub_task.label_set.filter(user=m).first()
                # Pass
                accept_label(label, label.sub_task.task)
    del request.session['answers_data']
    messages.success(request, '批量通过成功!')
    return redirect("/check_task/")
