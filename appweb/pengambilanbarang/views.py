from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from django.core.files.storage import FileSystemStorage
from .models import *
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def ambilbarang(request):
    # Periksa apakah pengguna sudah login
    if 'user_info' not in request.session:
        # Jika tidak, redirect ke halaman login
        return redirect('login_user')

    # Dapatkan informasi pengguna dari sesi
    user_info = request.session['user_info']
    nama = user_info['nama_user']

    if request.method == 'POST':
        departemen = request.POST.get('departemen')

        gambar_serah = request.FILES.get('gambar_serah')
        if gambar_serah:
            fs = FileSystemStorage()
            filename = fs.save(f'pengambilanbarang/static/img_serah/{gambar_serah.name}', gambar_serah)
            gambar_serah_path = fs.url(filename)
        else:
            gambar_serah_path = None

        keterangan_pengambil = request.POST.get('keterangan_pengambil')
        jumlah_barang = int(request.POST.get('quantity', 0))

        try:
            # Cari pengguna berdasarkan nama pada formulir
            selected_user = TbUser.objects.get(nama_user=user_info['nama_user'])
        except ObjectDoesNotExist:
            # Tangani jika pengguna tidak ditemukan
            messages.error(request, 'Pengguna tidak ditemukan.')
            return redirect('ambilbarang')

        tanggal_utc = timezone.now()
        tanggal_formatted = timezone.localtime(tanggal_utc)

        nama_barang_list = request.POST.getlist('barang_nama[]')
        jumlah_list = request.POST.getlist('barang_jumlah[]')
        satuan_list = request.POST.getlist('barang_satuan[]')

        ambilbarangform = TbAmbilbarangform.objects.create(
            tanggal=tanggal_formatted,
            nama=selected_user,
            departemen=departemen,
            gambar_serah=gambar_serah_path,
            keterangan_pengambil=keterangan_pengambil
        )

        barang_instances = []

        for nama_barang, jumlah, satuan in zip(nama_barang_list, jumlah_list, satuan_list):
            try:
                tb_ambilbarangket = TbAmbilbarangket(
                    no_ambil=ambilbarangform,
                    nama_barang=nama_barang,
                    jumlah=jumlah,
                    satuan=satuan
                )
                tb_ambilbarangket.save()
                barang_instances.append(tb_ambilbarangket)
                print(f"Data berhasil masuk ke TbAmbilbarangket: {tb_ambilbarangket}")
            except IntegrityError as e:
                if 'Duplicate entry' in str(e):
                    print("")
                else:
                    print(f"Error saat menyimpan ke TbAmbilbarangket: {e}")

        try:
            with transaction.atomic():
                TbAmbilbarangket.objects.bulk_create(barang_instances)
        except IntegrityError as e:
            if 'Duplicate entry' in str(e):
                print(".")
            else:
                print(f"Error saat menyimpan ke TbAmbilbarangket: {e}")
        
        # Mengarahkan pengguna ke statusambilbarang.html setelah submit
        return redirect('statusambilbarang')

    context = {
        'user_info': user_info,
        'nama_user': user_info['nama_user']
    }
    return render(request, 'ambilbarang.html', context)


def statusambilbarang(request):
    # Periksa apakah pengguna sudah login
    if 'user_info' not in request.session:
        # Jika tidak, redirect ke halaman login
        return redirect('login_user')

    # Dapatkan informasi pengguna dari sesi
    user_info = request.session['user_info']
    jabatan = user_info['jabatan']

    if jabatan == 'Admin':
            unique_no_ambil = TbAmbilbarangform.objects.values_list('no_ambil', flat=True).distinct()
            # Ubah urutan berdasarkan kolom tanggal dengan tanda '-' untuk urutan dari yang terbaru
            status_list = TbAmbilbarangform.objects.filter(no_ambil__in=unique_no_ambil).order_by('-tanggal')
    else:
        status_list = TbAmbilbarangform.objects.filter(nama=user_info['user_id']).order_by('-tanggal')
    
    paginator = Paginator(status_list, 5)  # Ubah 5 dengan jumlah item per halaman yang diinginkan

    page = request.GET.get('page')
    try:
        status_list = paginator.page(page)
    except PageNotAnInteger:
        status_list = paginator.page(1)
    except EmptyPage:
        status_list = paginator.page(paginator.num_pages)

    context = {
        'status_list': status_list,
        'user_info': user_info,
    }

    if request.method == 'POST':
        # Dapatkan informasi formulir upload gambar dokumen
        no_ambil = request.POST.get('no_ambil')
        gambar_dokum = request.FILES.get('gambar_dokum')
        keterangan_admin = request.POST.get('keterangan_admin') 

        try:
            # Cari status ambil barang berdasarkan nomor ambil
            selected_status = TbAmbilbarangform.objects.get(no_ambil=no_ambil)

            if jabatan == 'Admin':
                # Hanya Admin yang dapat mengisi keterangan_admin
                selected_status.keterangan_admin = keterangan_admin

            if gambar_dokum:
                fs = FileSystemStorage()
                filename = fs.save(f'pengambilanbarang/static/img_dokum/{gambar_dokum.name}', gambar_dokum)
                gambar_dokum_path = fs.url(filename)

                # Update atribut gambar_dokum pada objek TbAmbilbarangform yang sesuai
                selected_status.gambar_dokum = gambar_dokum_path
                selected_status.save()

                messages.success(request, 'Gambar dokumen berhasil diunggah.')
            else:
                messages.error(request, 'Silakan pilih gambar dokumen.')

            # Simpan perubahan pada keterangan_admin
            selected_status.save()

            messages.success(request, 'Data berhasil diperbarui.')

            return redirect('statusambilbarang')

        except TbAmbilbarangform.DoesNotExist:
            # Tangani jika status ambil barang tidak ditemukan
            messages.error(request, 'Status ambil barang tidak ditemukan.')

    return render(request, 'statusambilbarang.html', context)