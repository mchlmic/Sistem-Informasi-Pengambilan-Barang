# # Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from pengambilanbarang.models import TbUser, TbUserdetail
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.db import transaction
import bcrypt

def login_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        nama_user = request.POST.get('nama_user')

        # Cek apakah kombinasi user_id dan nama_user valid
        user_exists = TbUser.objects.filter(user_id=user_id, nama_user=nama_user).exists()

        if user_exists:
            # Ambil informasi user
            user_info = TbUser.objects.get(user_id=user_id)

            try:
                # Ambil informasi userdetail
                user_detail_info = TbUserdetail.objects.get(user_id=user_info)
            except TbUserdetail.DoesNotExist:
                # Tangani jika TbUserdetail tidak ada
                user_detail_info = None

            request.session['user_info'] = {
                'user_id': user_info.user_id,
                'nama_user': user_info.nama_user,
                'jabatan': user_info.jabatan,
                'departemen': user_info.departemen,
            }
            if user_detail_info:
                request.session['user_detail_info'] = {
                    'tempat_lahir': user_detail_info.tempat_lahir,
                    'tanggal_lahir': user_detail_info.tanggal_lahir.strftime('%Y-%m-%d') if user_detail_info.tanggal_lahir else None,
                    'alamat': user_detail_info.alamat,
                    'jenis_kelamin': user_detail_info.jenis_kelamin,
                    'nik': user_detail_info.nik,
                    'tanggal_masuk': user_detail_info.tanggal_masuk.strftime('%Y-%m-%d') if user_detail_info.tanggal_masuk else None,
                    'foto_user': user_detail_info.foto_user,
                    'e_mail': user_detail_info.e_mail,
                }
            else:
                # Atur user_detail_info ke None jika tidak ditemukan
                request.session['user_detail_info'] = None

            # Perbarui sesi secara manual
            request.session.modified = True

            return redirect('dashboard') 
            messages.error(request, 'Kombinasi user_id dan nama_user tidak valid.')

    return render(request, 'login.html')


def logout_user(request):
    # Hapus session yang berisi informasi pengguna
    if 'user_info' in request.session:
        del request.session['user_info']

    if 'user_detail_info' in request.session:
        del request.session['user_detail_info']

    # Redirect ke halaman login atau halaman lain yang diinginkan
    return redirect('login_user') 


def index(request):
    # Periksa apakah pengguna sudah login
    if 'user_info' not in request.session or 'user_detail_info' not in request.session:
        # Jika tidak, redirect ke halaman login
        return redirect('login_user')

    # Pengguna sudah login, dapatkan informasi dari sesi
    user_info = request.session['user_info']
    user_detail_info = request.session['user_detail_info']

    template = 'index.html'
    context = {
        'user_info': user_info,
        'user_detail_info': user_detail_info
    }
    return render(request, template, context)


def register_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        nama_user = request.POST.get('nama_user')
        jabatan = request.POST.get('jabatan')
        departemen = request.POST.get('departemen')
        password = request.POST.get('password')

        # Hash password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


        # Simpan TbUser
        user_info = TbUser.objects.create(
            user_id=user_id,
            nama_user=nama_user,
            jabatan=jabatan,
            departemen=departemen,
            password=hashed_password.decode('utf-8'),
        )

        # Simpan TbUserdetail
        TbUserdetail.objects.create(
            user_id=user_info,
        )

        messages.success(request, 'Pendaftaran berhasil. Silakan login.')
        return redirect('login_user')

    return render(request, 'register.html')

def register_detail(request):
    # Periksa apakah pengguna sudah login
    if 'user_info' not in request.session or 'user_detail_info' not in request.session:
        # Jika tidak, redirect ke halaman login
        return redirect('login_user')

    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            print(f'user_id: {user_id}')

            # Periksa apakah TbUser dengan user_id yang sesuai ada
            user_info = TbUser.objects.get(user_id=user_id)
            print(f'user_info: {user_info}')

            with transaction.atomic():
                # Update TbUser
                user_id = request.POST.get('user_id')
                user_info = TbUser.objects.get(user_id=user_id)
                user_info.nama_user = request.POST.get('nama_user')
                user_info.jabatan = request.POST.get('jabatan')
                user_info.departemen = request.POST.get('departemen')
                user_info.save()  # Simpan perubahan pada objek TbUser

                print(f'TbUser ID: {user_info.user_id}')
                print(f'Tempat Lahir: {request.POST.get("tempat_lahir")}')
                print(f'Tanggal Lahir: {request.POST.get("tanggal_lahir")}')
                print(f'Alamat: {request.POST.get("alamat")}')
                print(f'NIK: {request.POST.get("nik")}')
                print(f'Jenis Kelamin: {request.POST.get("jenis_kelamin")}')
                print(f'E-mail: {request.POST.get("e_mail")}')
                print(f'Tanggal Masuk: {request.POST.get("tanggal_masuk")}')
                print(f'Foto User: {request.FILES.get("foto_user")}')

                # Update TbUserdetail
                user_detail_info, created = TbUserdetail.objects.update_or_create(
                    user_id=user_info,
                    defaults={
                        'tempat_lahir' : request.POST.get('tempat_lahir'),
                        'tanggal_lahir': request.POST.get('tanggal_lahir'),
                        'alamat': request.POST.get('alamat'),
                        'jenis_kelamin': request.POST.get('jenis_kelamin'),
                        'nik': request.POST.get('nik'),
                        'tanggal_masuk': request.POST.get('tanggal_masuk'),
                        'e_mail': request.POST.get('e_mail'),
                    }
                )
                # Simpan foto_user
                foto_user = request.FILES.get('foto_user')
                if foto_user:
                    fs = FileSystemStorage()
                    filename = fs.save(f'user/static/foto_user/{foto_user.name}', foto_user)
                    user_detail_info.foto_user = fs.url(filename)
                    user_detail_info.save()

                messages.success(request, 'Perubahan berhasil disimpan.')
                print(request, 'Perubahan berhasil disimpan.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            print(request, f'Error: {str(e)}')
        
        # Perbarui sesi secara manual
        request.session.modified = True
        
        return redirect('dashboard')

    # Retrieve user and user_detail_info information
    user_info = request.session.get('user_info')
    user_detail_info = request.session.get('user_detail_info')

    # Print statements for debugging
    print("user_info:", user_info)
    print("user_detail_info:", user_detail_info)

    context = {
        'user_info': user_info,
        'user_detail_info': user_detail_info,
    }

    return render(request, 'registerdetail.html', context)


def userdata(request):
    # Periksa apakah pengguna sudah login
    if 'user_info' not in request.session:
        # Jika tidak, redirect ke halaman login
        return redirect('login_user')

    # Dapatkan informasi pengguna dari sesi
    user_info = request.session['user_info']
    jabatan = user_info['jabatan']

    if jabatan == 'Admin':
    # Mengambil data TbUser dan TbUserdetail
        user_data_list = TbUserdetail.objects.select_related("user_id").all()

    context = {
        'user_data_list': user_data_list,
        'user_info': user_info,
    }

    return render(request, 'userdata.html', context)