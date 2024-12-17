from django import forms
from .models import *
from django.db.models import Q
from django.utils import timezone

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['ten', 'mota', 'gia', 'chi_phi', 'tinhtrang'] 

class AddMenuItemForm(forms.Form):
    menu_item = forms.ModelChoiceField(queryset=Menu.objects.filter(tinhtrang=True), label="Chọn món")
    soluong = forms.IntegerField(min_value=1, label="Số lượng")

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'chucvu']  
        widgets = {
            'chucvu': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        if 'chucvu' in self.fields:
            self.fields['chucvu'].choices = [
                (key, value) for key, value in self.fields['chucvu'].choices if key != 'admin'
            ]
class BanForm(forms.ModelForm):
    class Meta:
        model = Ban
        fields = ['banso', 'tinhtrangban'] 

class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['tenKhach'] 

class LichLamViecForm(forms.ModelForm):
    class Meta:
        model = LichLamViec
        fields = ['nhanvien', 'ngay', 'ca']
    
    def __init__(self, *args, **kwargs):
        super(LichLamViecForm, self).__init__(*args, **kwargs)

        self.fields['nhanvien'].queryset = CustomUser.objects.filter(Q(chucvu='bep') | Q(chucvu='phucvu'))
        current_time = timezone.localtime(timezone.now()).date()
        self.fields['ngay'].widget = forms.DateInput(attrs={
            'type': 'date',
            'min': current_time  
        })