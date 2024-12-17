from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from datetime import time
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    """
    Lớp người dùng kế thừa từ AbstractUser, dùng để quản lý nhân viên
    Các thuộc tính:
        VaiTro_NhanVien: Tuple chứa các lựa chọn vai trò của nhân viên
        chucvu: Trường để lưu vai trò của nhân viên, mặc định là 'phucvu'
        groups: Một mối quan hệ nhiều-nhiều với nhóm người dùng
        user_permissions: Một mối quan hệ nhiều-nhiều với quyền người dùng
    """
    VaiTro_NhanVien = [
        ('quanly', 'Quản Lý'),
        ('bep', 'Bếp'),
        ('phucvu', 'Phục Vụ'),
        ('admin', 'Admin'),
    ]

    chucvu = models.CharField(max_length=20, choices=VaiTro_NhanVien, default='phucvu')
    
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
    )
    
    def get_full_name(self):
        """
        Trả về tên đầy đủ của nhân viên

        Return:
            str: Tên đầy đủ của nhân viên.
        """
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        """
        Trả về chuỗi mô tả nhân viên, bao gồm ID, tên đầy đủ và chức vụ

        Return:
            str: Mô tả nhân viên
        """
        return f"{self.id} - {self.get_full_name()} - {self.get_chucvu_display()}"

    class Meta:
        db_table = 'rm_customuser'
        verbose_name = "Nhân viên"
        verbose_name_plural = "Nhân viên"
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'], name="unique_user")
        ]

class Ban(models.Model):
    """
    Lớp Bàn trong nhà hàng, bao gồm thông tin về số bàn và tình trạng của bàn

    Thuộc tính:
        banso: Số hiệu của bàn, phải là duy nhất
        tinhtrangban: Tình trạng của bàn, true nếu bàn có khách, false nếu bàn trống.
    """
    banso = models.IntegerField(unique=True)  
    tinhtrangban = models.BooleanField(default=False) 

    def __str__(self):
        return f"Bàn {self.banso} - {'Đang có khách' if self.tinhtrangban else 'Bàn trống'})"
    
class Menu(models.Model):
    """
    Lớp Menu của nhà hàng, bao gồm tên món ăn và thông tin liên quan

    Thuộc tính:
        LOAI_MON_CHOICES: Các loại món ăn (khai vị, món chính, tráng miệng)
        ten: Tên của món ăn
        mota: Loại món ăn
        gia: Giá của món ăn
        chi_phi: Chi phí của món ăn
        tinhtrang: Tình trạng món ăn, true nếu còn món, false nếu hết món
    """
    LOAI_MON_CHOICES = [
        ('starter', 'Khai vị'),
        ('main', 'Món chính'),
        ('dessert', 'Tráng miệng'),
    ]
    
    ten = models.CharField(max_length=100, verbose_name="Tên món ăn")
    mota = models.CharField(max_length=50, choices=LOAI_MON_CHOICES, default='main', verbose_name="Loại món")
    gia = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá")
    chi_phi = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Chi phí")
    tinhtrang = models.BooleanField(default=True, verbose_name="Trạng thái")

    
    @property
    def loinhuanmon(self):
        """
        Tính lợi nhuận món ăn 

        Return:
            Decimal: Lợi nhuận món ăn
        """ 
        return self.gia - self.chi_phi
    
    def __str__(self):
        return f"{self.ten} - {self.get_mota_display()} - {self.gia} - {'Còn' if self.tinhtrang else 'Hết món'}"

class Order(models.Model):
    """
    Lớp Đơn hàng trong nhà hàng, bao gồm thông tin về tên khách, bàn, trạng thái đơn hàng và nhân viên phục vụ

    Thuộc tính:
        tenKhach: Tên khách hàng, mặc định là 'Khách lẻ'
        ban: Khóa ngoại liên kết với Bàn. Bàn mà nhân viên mở đơn hàng
        ngay: Ngày giờ tạo đơn hàng
        ngay_thanh_toan: Ngày giờ thanh toán 
        tinhtrang: Trạng thái thanh toán của đơn hàng, true nếu đã thanh toán, false nếu chưa thanh toán
        nhanvien_phucvu: Khóa ngoại liên kết với CustomUser. Nhân viên phục vụ cho đơn hàng này
    """
    tenKhach = models.CharField(max_length=100, default='Khách lẻ')
    ban = models.ForeignKey(Ban, on_delete=models.SET_NULL, null=True, blank=True)
    ngay = models.DateTimeField(auto_now_add=True)
    ngay_thanh_toan = models.DateTimeField(null=True, blank=True)  
    tinhtrang = models.BooleanField(default=False)
    nhanvien_phucvu = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Nhân viên phục vụ"
    )
    
    @property
    def tongtien(self):
        """
        Tính tổng tiền của đơn hàng 

        Return:
            Decimal: Tổng tiền của đơn hàng
        """
        return sum(item.gia * item.soluong for item in self.items.all())
    
    @property
    def loinhuan(self):
        """
        Tính lợi nhuận của đơn hàng

        Return:
            Decimal: Lợi nhuận của đơn hàng
        """
        return sum((item.menu_item.gia - item.menu_item.chi_phi) * item.soluong for item in self.items.all())
    
    def __str__(self):
        return f"Order so {self.id} cho KhachHang {self.tenKhach} - {'Da thanh toan' if self.tinhtrang else 'Chua thanh toan'}"
    
class ChiTietOrder(models.Model):
    """
    Lớp Chi tiết đơn hàng, lưu các món ăn trong một đơn hàng

    Thuộc tính:
        order: Khóa ngoại liên kết với (Order) 
        menu_item: Khóa ngoại liên kết với món ăn (Menu)
        soluong: Số lượng của món ăn
        gia: Giá của món ăn
        tinhtrang: Tình trạng của món ăn trong đơn (chưa lên món, đã lên món, đã nhận món)
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    soluong = models.PositiveIntegerField()
    gia = models.DecimalField(max_digits=10, decimal_places=0)
    
    TINH_TRANG_CHOICES = [
        ('chua_len', 'Chưa lên món'),
        ('da_len', 'Đã lên món'),
        ('da_nhan', 'Đã nhận món'),
    ]
    
    tinhtrang = models.CharField(
        max_length=10,
        choices=TINH_TRANG_CHOICES,
        default='chua_len',
        verbose_name='Trạng thái'
    )
    
    @property
    def thanh_tien(self):
        """
        Tính thành tiền của một món ăn trong chi tiết đơn hàng

        Return:
            Decimal: Thành tiền của món ăn
        """
        return self.gia * self.soluong
    
    def __str__(self):
        return f"{self.menu_item.ten} : {self.gia} x {self.soluong} = {self.thanh_tien}"
    
class LichLamViec(models.Model):
    """
    Lớp Lịch làm việc của nhân viên, quản lý ca làm việc và thời gian chấm công của nhân viên

    Thuộc tính:
        TRANG_THAI_CHOICES: Các trạng thái ca làm việc (chưa vào ca, trong ca, ra ca)
        nhanvien: Khóa ngoại liên kết với CustomUser. Nhân viên có lịch làm việc này
        ngay: Ngày làm việc
        ca: Ca làm việc (sáng, chiều)
        giovao: Thời gian vào ca
        giora: Thời gian ra ca
        trangthai_nhanvien: Trạng thái của nhân viên trong ca
    """
    TRANG_THAI_CHOICES = [
        ('chua_vaoca', 'Chưa vào ca'),
        ('trong_ca', 'Đang trong ca'),
        ('ra_ca', 'Đã ra ca'),
    ]
    nhanvien = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
    )
    ngay = models.DateField()
    ca = models.CharField(max_length=20, choices=[('sang', 'Sáng'), ('chieu', 'Chiều')])
    giovao = models.DateTimeField(null=True, blank=True) 
    giora = models.DateTimeField(null=True, blank=True) 
    trangthai_nhanvien = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='chua_vaoca',
    )
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(giora__gt=models.F('giovao')) | models.Q(giovao__isnull=True) | models.Q(giora__isnull=True),
                name='check_giora_giovao'
            ),
            models.UniqueConstraint(fields=['nhanvien', 'ngay', 'ca'], name='unique_employee_shift'),
        ]

    def __str__(self):
        giovao_str = self.giovao if self.giovao else "Chưa chấm công"
        giora_str = self.giora if self.giora else "Chưa chấm công"
        return f"{self.nhanvien.get_full_name()} - {self.nhanvien.chucvu} : {giovao_str} - {giora_str}"

    def get_shift_time_range(self):
        """
        Trả về khoảng thời gian cho ca làm việc dựa trên ca

        Return:
            tuple: Khoảng thời gian cho ca làm việc (start_time, end_time).
        """
        if self.ca == 'sang':
            return time(8, 0, 0), time(12, 0, 0) 
        elif self.ca == 'chieu':
            return time(13, 0, 0), time(17, 0, 0)
        return None
    
    def clean(self):
        """
        Kiểm tra vai trò của nhân viên trước khi lưu lịch làm việc

        Trả về:
            ValidationError: Nếu nhân viên có vai trò không hợp lệ
        """
        if self.nhanvien.chucvu not in ['quanly', 'bep', 'phucvu']:
            raise ValidationError("Nhân viên phải có vai trò là 'quanly', 'bep', hoặc 'phucvu'.")
        super().clean()



