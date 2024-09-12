# cython:language_level=3
import os
from pathlib import Path
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from api.models import RustDeskPeer, RustDesDevice, UserProfile, ShareLink, ConnLog, FileLog
from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.conf import settings

from itertools import chain
from django.db.models.fields import DateTimeField, DateField, CharField, TextField
import datetime
from django.db.models import Model
import json
import time
import hashlib
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
EFFECTIVE_SECONDS = 7200

def getStrSha256(s):
    input_bytes = s.encode('utf-8')
    sha256_hash = hashlib.sha256(input_bytes)
    return sha256_hash.hexdigest()

def model_to_dict2(instance, fields=None, exclude=None, replace=None, default=None):
    """
    :params instance: Model instance, cannot be a queryset
    :params fields: Specifies the fields to display, ('field1','field2')
    :params exclude: Specifies the fields to exclude, ('field1','field2')
    :params replace: Rename the database field names to the required names, {'database_field_name':'frontend_display_name'}
    :params default: Add new field data that doesn't exist, {'field':'data'}
    """
    # Validation for the model instance passed
    if not isinstance(instance, Model):
        raise Exception('model_to_dict expects a model instance')
    # Validation for replacing database field names
    if replace and type(replace) == dict:
        for replace_field in replace.values():
            if hasattr(instance, replace_field):
                raise Exception(f'model_to_dict, the field {replace_field} to be replaced already exists')
    # Validation for adding default values
    if default and type(default) == dict:
        for default_key in default.keys():
            if hasattr(instance, default_key):
                raise Exception(f'model_to_dict, adding a default value for field {default_key} but it already exists')
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        # Original code: this part of code would exclude date fields, added a condition to include them
        if not getattr(f, 'editable', False):
            if type(f) == DateField or type(f) == DateTimeField:
                pass
            else:
                continue
        # If fields parameter is passed, it needs to be checked
        if fields is not None and f.name not in fields:
            continue
        # If exclude is passed, it needs to be checked
        if exclude and f.name in exclude:
            continue

        key = f.name
        # Getting the data for the field
        if type(f) == DateTimeField:
            # If the field type is DateTimeField, handle it in a specific way
            value = getattr(instance, key)
            value = datetime.datetime.strftime(value, '%Y-%m-%d')
        elif type(f) == DateField:
            # If the field type is DateField, handle it in a specific way
            value = getattr(instance, key)
            value = datetime.datetime.strftime(value, '%Y-%m-%d')
        elif type(f) == CharField or type(f) == TextField:
            # Check if string data can be serialized into Python structures
            value = getattr(instance, key)
            try:
                value = json.loads(value)
            except Exception as _:
                value = value
        else: # For other types of fields
            key = f.name
            value = f.value_from_object(instance)
        # 1. Replace field names
        if replace and key in replace.keys():
            key = replace.get(key)
        data[key] = value
    # 2. Add new default field data
    if default:
        data.update(default)
    return data

def index(request):
    print('debug',sys.argv)
    if request.user and request.user.username!='AnonymousUser':
        return HttpResponseRedirect('/api/work')
    return HttpResponseRedirect('/api/user_action?action=login')

def user_action(request):
    action = request.GET.get('action', '')
    if action == '':
        return
    if action == 'login':
        return user_login(request)
    if action == 'register':
        return user_register(request)
    if action == 'logout':
        return user_logout(request)

def user_login(request):
    # Handles user login
    if request.method == 'GET':
        return render(request, 'login.html')

    username = request.POST.get('account', '')
    password = request.POST.get('password', '')
    if not username or not password:
        return JsonResponse({'code':0, 'msg':'There was a problem.'})

    user = auth.authenticate(username=username,password=password)
    if user:
        auth.login(request, user)
        return JsonResponse({'code':1, 'url':'/api/work'})
    else:
        return JsonResponse({'code':0, 'msg':'Account or password incorrect!'})

def user_register(request):
    # Handles user registration
    info = ''
    if request.method == 'GET':
        return render(request, 'reg.html')

    result = {
        'code':0,
        'msg':''
    }
    username = request.POST.get('user', '')
    password1 = request.POST.get('pwd', '')

    if len(username) <= 3:
        info = 'Username must be longer than 3 characters'
        result['msg'] = info
        return JsonResponse(result)

    if len(password1)<8 or len(password1)>20:
        info = 'Password length does not meet requirements, should be 8~20 characters.'
        result['msg'] = info
        return JsonResponse(result)

    user = UserProfile.objects.filter(Q(username=username)).first()
    if user:
        info = 'Username already exists.'
        result['msg'] = info
        return JsonResponse(result)
    user = UserProfile(
        username=username,
        password=make_password(password1),
        is_admin = True if UserProfile.objects.count()==0 else False,
        is_superuser = True if UserProfile.objects.count()==0 else False,
        is_active = True
    )
    user.save()
    result['msg'] = info
    result['code'] = 1
    return JsonResponse(result)

@login_required(login_url='/api/user_action?action=login')
def user_logout(request):
    # Handles user logout
    info = ''
    auth.logout(request)
    return HttpResponseRedirect('/api/user_action?action=login')
        
def get_single_info(uid):
    # Fetches single user information
    peers = RustDeskPeer.objects.filter(Q(uid=uid))
    rids = [x.rid for x in peers]
    peers = {x.rid:model_to_dict(x) for x in peers}
    devices = RustDesDevice.objects.filter(rid__in=rids)
    devices = {x.rid:x for x in devices}

    for rid, device in devices.items():
        peers[rid]['create_time'] = device.create_time.strftime('%Y-%m-%d')
        peers[rid]['update_time'] = device.update_time.strftime('%Y-%m-%d')
        peers[rid]['version'] = device.version
        peers[rid]['memory'] = device.memory
        peers[rid]['cpu'] = device.cpu
        peers[rid]['os'] = device.os

    for rid in peers.keys():
        peers[rid]['has_rhash'] = 'Yes' if len(peers[rid]['rhash'])>1 else 'No'

    return [v for k,v in peers.items()]

def get_all_info():
    # Fetches all device and peer information
    devices = RustDesDevice.objects.all()
    peers = RustDeskPeer.objects.all()
    devices = {x.rid:model_to_dict2(x) for x in devices}
    for peer in peers:
        user = UserProfile.objects.filter(Q(id=peer.uid)).first()
        device = devices.get(peer.rid, None)
        if device:
            devices[peer.rid]['rust_user'] = user.username
    return [v for k,v in devices.items()]

@login_required(login_url='/api/user_action?action=login')
def work(request):
    # Main work view
    username = request.user
    u = UserProfile.objects.get(username=username)
    single_info = get_single_info(u.id)

    all_info = get_all_info()
    print(all_info)

    return render(request, 'show_work.html', {'single_info':single_info, 'all_info':all_info, 'u':u})

def check_sharelink_expired(sharelink):
    # Checks if a share link is expired
    now = datetime.datetime.now()
    if sharelink.create_time > now:
        return False
    if (now - sharelink.create_time).seconds <15 * 60:
        return False
    else:
        sharelink.is_expired = True
        sharelink.save()
        return True

@login_required(login_url='/api/user_action?action=login')
def share(request):
    # Share view for handling peer sharing and share link management
    peers = RustDeskPeer.objects.filter(Q(uid=request.user.id))
    sharelinks = ShareLink.objects.filter(Q(uid=request.user.id) & Q(is_used=False) & Q(is_expired=False))

    # Optimize resources: Handle expired requests, check for expiry on any request instead of running a cron job.
    now = datetime.datetime.now()
    for sl in sharelinks:
        check_sharelink_expired(sl)
    sharelinks = ShareLink.objects.filter(Q(uid=request.user.id) & Q(is_used=False) & Q(is_expired=False))
    peers = [{'id':ix+1, 'name':f'{p.rid}|{p.alias}'} for ix, p in enumerate(peers)]
    sharelinks = [{'shash':s.shash, 'is_used':s.is_used, 'is_expired':s.is_expired, 'create_time':s.create_time, 'peers':s.peers} for ix, s in enumerate(sharelinks)]

    if request.method == 'GET':
        url = request.build_absolute_uri()
        if url.endswith('share'):
            return render(request, 'share.html', {'peers':peers, 'sharelinks':sharelinks})
        else:
            shash = url.split('/')[-1]
            sharelink = ShareLink.objects.filter(Q(shash=shash))
            msg = ''
            title = 'Success'
            if not sharelink:
                title = 'Error'
                msg = f'Link {url}:<br>The share link does not exist or has expired.'
            else:
                sharelink = sharelink[0]
                if str(request.user.id) == str(sharelink.uid):
                    title = 'Error'
                    msg = f'Link {url}:<br><br>You can not share the link with yourself, can you ! '
                else:
                    sharelink.is_used = True
                    sharelink.save()
                    peers = sharelink.peers
                    peers = peers.split(',')
                    # Skip if one's own peers overlap
                    peers_self_ids = [x.rid for x in RustDeskPeer.objects.filter(Q(uid=request.user.id))]
                    peers_share = RustDeskPeer.objects.filter(Q(rid__in=peers) & Q(uid=sharelink.uid))
                    peers_share_ids = [x.rid for x in peers_share]

                    for peer in peers_share:
                        if peer.rid in peers_self_ids:
                            continue
                        
                        peer_f = RustDeskPeer.objects.filter(Q(rid=peer.rid) & Q(uid=sharelink.uid))
                        if not peer_f:
                            msg += f"{peer.rid} already exists,"
                            continue
                        
                        if len(peer_f) > 1:
                             msg += f'{peer.rid} has multiple instances, skipped. '
                             continue
                        peer = peer_f[0]
                        peer.id = None
                        peer.uid = request.user.id
                        peer.save()
                        msg += f"{peer.rid},"

                    msg += 'has been successfully acquired.'

            return render(request, 'msg.html', {'title':msg, 'msg':msg})
    else:
        data = request.POST.get('data', '[]')

        data = json.loads(data)
        if not data:
            return JsonResponse({'code':0, 'msg':'Data is empty.'})
        rustdesk_ids = [x['title'].split('|')[0] for x in data]
        rustdesk_ids = ','.join(rustdesk_ids)
        sharelink = ShareLink(
            uid=request.user.id,
            shash = getStrSha256(str(time.time())+settings.SALT_CRED),
            peers=rustdesk_ids,
        )
        sharelink.save()

        return JsonResponse({'code':1, 'shash':sharelink.shash})

@login_required(login_url='/api/user_action?action=login')
def installers(request):
    return render(request, 'installers.html')

def get_conn_log():
    logs = ConnLog.objects.all()
    logs = {x.id:model_to_dict(x) for x in logs}

    for k, v in logs.items():
        try:
            peer = RustDeskPeer.objects.get(rid=v['rid'])
            logs[k]['alias'] = peer.alias
        except:
            logs[k]['alias'] = 'UNKNOWN'
        try:
            peer = RustDeskPeer.objects.get(rid=v['from_id'])
            logs[k]['from_alias'] = peer.alias
        except:
            logs[k]['from_alias'] = 'UNKNOWN'
        #from_zone = tz.tzutc()
        #to_zone = tz.tzlocal()
        #utc = logs[k]['logged_at']
        #utc = utc.replace(tzinfo=from_zone)
        #logs[k]['logged_at'] = utc.astimezone(to_zone)
        try:
            duration = round((logs[k]['conn_end'] - logs[k]['conn_start']).total_seconds())
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            #d, h = divmod(h, 24)
            logs[k]['duration'] = f'{h:02d}:{m:02d}:{s:02d}'
        except:
            logs[k]['duration'] = -1

    sorted_logs = sorted(logs.items(), key=lambda x: x[1]['conn_start'], reverse=True)
    new_ordered_dict = {}
    for key, alog in sorted_logs:
        new_ordered_dict[key] = alog

    return [v for k, v in new_ordered_dict.items()]

def get_file_log():
    logs = FileLog.objects.all()
    logs = {x.id:model_to_dict(x) for x in logs}

    for k, v in logs.items():
        try:
            peer_remote = RustDeskPeer.objects.get(rid=v['remote_id'])
            logs[k]['remote_alias'] = peer_remote.alias
        except:
            logs[k]['remote_alias'] = 'UNKNOWN'
        try:
            peer_user = RustDeskPeer.objects.get(rid=v['user_id'])
            logs[k]['user_alias'] = peer_user.alias
        except:
            logs[k]['user_alias'] = 'UNKNOWN'

    sorted_logs = sorted(logs.items(), key=lambda x: x[1]['logged_at'], reverse=True)
    new_ordered_dict = {}
    for key, alog in sorted_logs:
        new_ordered_dict[key] = alog

    return [v for k, v in new_ordered_dict.items()]

@login_required(login_url='/api/user_action?action=login')
def conn_log(request):
    paginator = Paginator(get_conn_log(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'show_conn_log.html', {'page_obj':page_obj})

@login_required(login_url='/api/user_action?action=login')
def file_log(request):
    paginator = Paginator(get_file_log(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'show_file_log.html', {'page_obj':page_obj})

@login_required(login_url='/api/user_action?action=login')
def clients(request):
    basedir = os.path.join('clients')
    custom = os.path.join(basedir,'custom')
    client_custom_files = {}
    
    if os.path.exists(custom):
        for file in os.listdir(custom):
            if file.endswith(".exe"):
                filepath = os.path.join(custom,file)
                modified = datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %I:%M:%S %p')
                client_custom_files[file] = {
                    'file': file,
                    'modified': modified,
                    'path': custom
                }
    return render(request, 'clients.html', {'client_custom_files': client_custom_files})

def download_file(request, filename, path):
    file_path = os.path.join(str(BASE_DIR),path,filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/x-binary',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })
    return response

@login_required(login_url='/api/user_action?action=login')
def download(request):
    filename = request.GET['filename']
    path = request.GET['path']
    return download_file(request, filename, path)

@login_required(login_url='/api/user_cation?action=login')
def delete_file(request):
    filename = request.GET['filename']
    path = request.GET['path']
    file_path = os.path.join(str(BASE_DIR),path,filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
    return HttpResponseRedirect('/api/clients')
