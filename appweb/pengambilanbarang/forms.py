# dalam file forms.py

from django import forms
from django.forms import formset_factory

class AmbilBarangForm(forms.Form):
    tanggal = forms.DateTimeField()
    nama = forms.CharField(max_length=25)
    departemen = forms.CharField(max_length=25)
    gambar_serah = forms.IntegerField()
    keterangan = forms.CharField(widget=forms.Textarea)
    jumlah_barang = forms.IntegerField(min_value=1)

AmbilBarangFormset = formset_factory(AmbilBarangForm, extra=1)
