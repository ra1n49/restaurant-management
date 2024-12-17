from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Case, When, Value, IntegerField, Q
from datetime import timedelta

# Create your views here.

@login_required
def all_employees(request):
    """
    Hiển thị danh sách nhân viên, lọc và sắp xếp theo vai trò của người dùng hiện tại.

    Nếu người dùng là 'bếp', 'phục vụ', hoặc 'quản lý', chỉ hiển thị nhân viên có vai trò tương ứng 
    Nếu là admin, hiển thị tất cả nhân viên và sắp xếp theo thứ tự vai trò 

    Input:
        request

    Return:
        HttpResponse: Trang HTML với danh sách nhân viên đã được lọc và sắp xếp
        Context:
            employees: Danh sách nhân viên đã lọc và sắp xếp
    """
    current_user = request.user

    if current_user.chucvu in ['bep', 'phucvu', 'quanly']:
        employees = CustomUser.objects.filter(chucvu__in=['bep', 'phucvu','quanly'])
    else:
        employees = CustomUser.objects.all()
    
    employees = employees.annotate(
        chucvu_order=Case(
            When(chucvu='admin', then=Value(1)),
            When(chucvu='quanly', then=Value(2)),
            default=Value(3), 
            output_field=IntegerField()
        )
    ).order_by('chucvu_order')

    return render(request, 'rm/all_employees.html', {'employees': employees})

def search_nhanvien_view(request):
    """
    Tìm kiếm nhân viên theo từ khóa và chức vụ của người dùng
    Phương thức lọc nhân viên theo các trường: tên đăng nhập, họ tên, email và chức vụ
    Kết quả tìm kiếm sẽ được lọc theo từ khóa

    Input:
        request

    Returns:
        HttpResponse: Trang HTML với danh sách nhân viên đã lọc
        Context:
            employees: Danh sách nhân viên đã lọc
            query: Từ khóa tìm kiếm
    """
    query = request.GET.get('q', '')
    current_user = request.user
    
    if current_user.chucvu in ['bep', 'phucvu', 'quanly']:
        employees = CustomUser.objects.filter(chucvu__in=['bep', 'phucvu','quanly'])
    else:
        employees = CustomUser.objects.all()

    if query:
        employees = employees.filter(
            Q(username__icontains=query) |  
            Q(first_name__icontains=query) |  
            Q(last_name__icontains=query) |  
            Q(email__icontains=query) |  
            Q(chucvu__in=[choice[0] for choice in CustomUser.VaiTro_NhanVien 
                          if query.lower() in choice[1].lower()])
        )

    return render(request, 'rm/all_employees.html', {
        'employees': employees,
        'query': query
    })

def add_employee(request):
    """
    Thêm nhân viên mới vào hệ thống. Tạo tài khoản với username tự động và mật khẩu mặc định là '123'
    Nếu chức vụ là 'bep', 'quanly', hoặc 'phucvu', nhân viên sẽ được gán quyền staff

    Input:
        request

    Output:
        Thêm thành công: Chuyển hướng về trang "all_employees" 
        Thất bại: Hiển thị thông báo lỗi
    """
    max_id = CustomUser.objects.all().aggregate(models.Max('id'))['id__max']
    next_id = max_id + 1 if max_id else 1  

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.username = str(next_id)  
            employee.set_password('123')  
            if employee.chucvu in ['bep', 'quanly','phucvu']:
                employee.is_staff = True
            else:
                employee.is_staff = False
            employee.save()  
            return redirect("all_employees") 
        else:
            messages.error(request, "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.")
    else:
        form = EmployeeForm()

    return render(request, "rm/add_employee.html", 
                  {"form": form, 
                   "next_id": next_id,})

def edit_employee(request, pk):
    """
    Cập nhật thông tin nhân viên theo ID 
    Nếu có thay đổi, thông tin nhân viên sẽ được lưu lại và kiểm tra chức vụ để cập nhật quyền staff

    Input:
        request
        pk: ID của nhân viên 

    Output:
        Chuyển hướng về trang "all_employees" nếu thông tin nhân viên cập nhật thành công
        Nếu dữ liệu không hợp lệ, hiển thị thông báo lỗi
    """
    employee = get_object_or_404(CustomUser, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)
            if employee.chucvu in ['bep', 'quanly','phucvu']:
                employee.is_staff = True
            else:
                employee.is_staff = False
            form.save()
            return redirect("all_employees")
        else:
            messages.error(request, "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "rm/edit_employee.html", {"form": form, "employee": employee})

def delete_employee(request, pk):
    """
    Xóa nhân viên theo ID

    Input:
        request
        pk: ID của nhân viên

    Output:
        Chuyển hướng về trang "all_employees" nếu nhân viên xóa thành công
    """
    if request.method == "POST":
        employee = get_object_or_404(CustomUser, pk=pk)
        employee.delete()
        return redirect("all_employees") 

    return redirect("all_employees")

def calamviec_nv(request, employee_id):
    """
    Hiển thị danh sách ca làm việc đã hoàn thành của nhân viên và tính tổng số giờ làm việc

    Input:
        request
        employee_id: ID của nhân viên 

    Output:
        Giao diện HTML hiển thị danh sách ca làm việc của nhân viên và tổng số giờ làm việc
    """
    employee = get_object_or_404(CustomUser, pk=employee_id)
    
    ca = LichLamViec.objects.filter(nhanvien=employee, trangthai_nhanvien='ra_ca').order_by('ngay','-ca')
    tongcong = timedelta()
    
    for shift in ca:
        tongcong += shift.giora - shift.giovao
        
    
    tongcong_str = str(tongcong)
    hours, minutes = tongcong_str.split(":")[:2]

    return render(request, 'rm/employee_shifts.html', {'employee': employee, 'ca': ca, 'total_hours': f"{hours}:{minutes}"})
# ----------------------------------------------------
@csrf_exempt
def custom_login(request):
    """
    Xử lý đăng nhập của người dùng. Kiểm tra tên đăng nhập và mật khẩu, sau đó chuyển hướng đến trang chủ nếu thành công

    Input:
        request

    Output:
        Chuyển hướng về trang "home" nếu đăng nhập thành công
        Nếu thông tin đăng nhập sai, hiển thị thông báo lỗi
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home") 
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")

    return render(request, "rm/login.html")

def logout_user(request):
    """
    Đăng xuất người dùng hiện tại và chuyển hướng về trang chủ

    Input:
        request

    Output:
        Chuyển hướng về trang chủ sau khi người dùng được đăng xuất
    """
    logout(request)
    return redirect("/")

@login_required
def Home(request):
    """
    Trang chủ dành cho người dùng đã đăng nhập

    Input:
        request

    Output:
        Giao diện HTML hiển thị trang chủ cho user đã đăng nhập
    """
    return render(request,'rm/home.html')
# ----------------------------------------------------
@login_required
def ban_view(request):
    """
    Xem danh sách bàn và cập nhật trạng thái bàn

    Input:
        request

    Output:
        Giao diện HTML hiển thị danh sách bàn và trạng thái của bàn
    """
    nhanvien_phucvu = request.user

    nhanvien_trong_ca = LichLamViec.objects.filter(nhanvien=nhanvien_phucvu, trangthai_nhanvien='trong_ca').exists()
    if request.method == "POST":
        ban_id = request.POST.get('ban_id')
   
        if ban_id:
            ban = get_object_or_404(Ban, id=ban_id)
            ban.tinhtrangban = True
            ban.save()
        
            order, created= Order.objects.get_or_create(ban=ban, tinhtrang=False)
            
            nhanvien_phucvu = request.user

            order.nhanvien_phucvu = nhanvien_phucvu
            order.save()
            
            return redirect('order_detail', ban_id = ban.id)  
    
    ban_items= Ban.objects.all()
    return render(request, 'rm/ban.html', {'ban_items': ban_items,
                                           'nhanvien_trong_ca': nhanvien_trong_ca})
def search_ban_view(request):
    """
    Tìm kiếm bàn theo số bàn hoặc trạng thái

    Input:
        request

    Output:
        Giao diện HTML hiển thị kết quả tìm kiếm 
    """
    query = request.GET.get('q', '')
    ban_items = Ban.objects.all()

    if query:
        ban_items = ban_items.filter(
            Q(banso__icontains=query) |  
            Q(tinhtrangban=True if 'đang sử dụng' in query.lower() else 
             False if 'trống' in query.lower() else None)
        )
        

    return render(request, 'rm/ban.html', {
        'ban_items': ban_items,
        'query': query
    })

def add_ban(request):
    """
    Thêm bàn mới vào hệ thống

    Input:
    request 

    Output:
        Chuyển hướng về trang "ban_view" nếu bàn được thêm thành công   
    """
    if request.method == "POST":
        form = BanForm(request.POST)
        if form.is_valid():
            form.save()  
            return redirect('ban_view')  
    else:
        form = BanForm() 
    
    return render(request, 'rm/add_ban.html', {'form': form})

def edit_ban(request, ban_id):
    """
    Chỉnh sửa thông tin bàn theo ID

    Input:
        request 
        ban_id: ID của bàn cần chỉnh sửa.   

    Output:
        Chuyển hướng về trang "ban_view" nếu thông tin bàn cập nhật thành công 
    """
    ban = get_object_or_404(Ban, id=ban_id) 
    if request.method == "POST":
        form = BanForm(request.POST, instance=ban) 
        if form.is_valid():
            form.save()  
            return redirect('ban_view') 
    else:
        form = BanForm(instance=ban)  
    
    return render(request, 'rm/edit_ban.html', {'form': form, 'ban': ban})

def delete_ban(request, ban_id):
    """
    Xóa bàn theo ID 

    Input:
        request  
        ban_id: ID của bàn cần xóa  

    Output:
        Chuyển hướng về trang "ban_view" nếu bàn được xóa thành công    
    """
    ban = get_object_or_404(Ban, id=ban_id)  
    if request.method == "POST": 
        ban.delete() 
        return redirect('ban_view')  
    
    return render(request, 'rm/delete_ban.html', {'ban': ban})
# ----------------------------------------------------

def quy_hoach_combo_loi_nhuan():
    """
    Tìm combo món ăn với lợi nhuận cao nhất từ menu hiện có

    Input:
        list: Khai vị, món chính, tráng miệng
    Output:
        Combo
        Lợi nhuận cao nhất từ combo
    """
    khai_vi = list(Menu.objects.filter(mota='starter', tinhtrang=True))
    mon_chinh = list(Menu.objects.filter(mota='main', tinhtrang=True))
    trang_mieng = list(Menu.objects.filter(mota='dessert', tinhtrang=True))

    all_items = [khai_vi, mon_chinh, trang_mieng]

    n = len(all_items) 
    dp = [{} for _ in range(n)]  

    for starter in all_items[0]:
        loinhuanmon = starter.gia - starter.chi_phi
        dp[0][(starter,)] = loinhuanmon

 
    for i in range(1, n):
        for prev_combo, prev_profit in dp[i - 1].items():
            for current_item in all_items[i]:
               
                loinhuanmon = current_item.gia - current_item.chi_phi

                new_combo = prev_combo + (current_item,)
                new_profit = prev_profit + loinhuanmon

                if new_combo not in dp[i] or dp[i][new_combo] < new_profit:
                    dp[i][new_combo] = new_profit

    max_profit = float('-inf')
    best_combo = None

    for combo, profit in dp[-1].items():
        if profit > max_profit:
            max_profit = profit
            best_combo = combo

    return {
        'combo': best_combo,
        'loi_nhuan': max_profit
    }

@login_required
def menu_view(request): 
    """
    Hiển thị menu của nhà hàng
    
    Input:
        request 
    
    Output:
        Giao diện HTML hiển thị danh sách món ăn từ menu, combo với lợi nhuận cao nhất và tổng lợi nhuận    
    """
    result = quy_hoach_combo_loi_nhuan()

    combo = result['combo']

    loi_nhuan = result['loi_nhuan']
    menu_items = Menu.objects.all()  
    return render(request, 'rm/menu.html', { 'menu_items' : menu_items,
                                            'combo': combo,
                                            'loi_nhuan': loi_nhuan})

def search_menu_view(request):
    """
    Tìm kiếm món ăn trong menu 
    
    Input:
        request 
    
    Output:
        Giao diện HTML hiển thị kết quả tìm kiếm từ menu 
    """
    query = request.GET.get('q', '')
    menu_items = Menu.objects.all()

    if query:
        menu_items = menu_items.filter(
            Q(ten__icontains=query) |  
            Q(mota__in=[choice[0] for choice in Menu.LOAI_MON_CHOICES 
                        if query.lower() in choice[1].lower()]) |
            Q(gia__icontains=query) |  
            Q(tinhtrang=True if 'còn' in query.lower() else 
             False if 'hết' in query.lower() else None)
        )
        

    return render(request, 'rm/menu.html', {
        'menu_items': menu_items,
        'query': query
    })

def add_menu_view(request):
    """
    Thêm món ăn mới vào menu
    
    Input:
    
    Output:
        Chuyển hướng về trang menu nếu món ăn được thêm thành công
        Hiển thị form để người dùng nhập món ăn mới nếu không phải là POST request
    """
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            form.save()  
            return redirect('menu') 
    else:
        form = MenuForm()  

    return render(request, 'rm/themFood.html', {'form': form})

def edit_menu_view(request, menu_id):
    """
    Chỉnh sửa thông tin của món ăn trong menu
    
    Input:
        request 
        menu_id: ID món ăn cần chỉnh sửa
    
    Output:
        Chuyển hướng về trang menu nếu món ăn được cập nhật thành công
        Hiển thị form để người dùng cập nhật món ăn nếu không phải là POST request
    """
    menu = get_object_or_404(Menu, id=menu_id) 
    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)  
        if form.is_valid():
            form.save()  
            return redirect('menu')  
    else:
        form = MenuForm(instance=menu)  

    return render(request, 'rm/suaFood.html', {'form': form})

def delete_menu_view(request, menu_id):
    """
    Xóa món ăn khỏi menu
    
    Input:
        menu_id: ID món ăn cần xóa    
    
    Output:
        Chuyển hướng về trang menu sau khi món ăn được xóa thành công
    """
    menu = get_object_or_404(Menu, id=menu_id) 
    menu.delete() 
    return redirect('menu') 
# ----------------------------------------------------
@login_required
def order_view(request):
    """
    Xem danh sách các đơn hàng đã thanh toán
    
    Input:
        request: Đối tượng HTTP request từ người dùng đã đăng nhập với quyền 'quanly' hoặc 'admin'  
    
    Output:
        Giao diện HTML hiển thị danh sách đơn hàng và tổng lợi nhuận các đơn hàng đã thanh toán
    """
    if request.user.chucvu not in ['quanly', 'admin']:
        messages.error(request, "Bạn không có quyền truy cập vào trang này.")  
        return redirect('/home/') 
    orders = Order.objects.filter(tinhtrang=True).order_by('ngay_thanh_toan')

    total_loinhuan = sum(order.loinhuan for order in orders)

    return render(request, 'rm/doanhthu.html', {
        'orders': orders,
        'total_loinhuan': total_loinhuan,
    })

def search_order_detail_dapaid(request):
    """
    Tìm đơn hàng đã thanh toán theo bàn, hóa đơn hoặc thông tin khác
    
    Input:
        request 
    
    Output:
        Giao diện HTML hiển thị kết quả tìm kiếm chi tiết đơn hàng 
    """
    query = request.GET.get('q', '')
    orders = Order.objects.filter(tinhtrang=True)

    if query:
       if query.lower().startswith('bàn '):
           try:
               ban_so = query.lower().replace('bàn ', '').strip()
               orders = orders.filter(ban__banso=int(ban_so))
           except ValueError:
               orders = orders.none()
       elif query.lower().startswith('hóa đơn'):
           try:
               order_id = query.lower().replace('hóa đơn', '').strip()
               orders = orders.filter(id=int(order_id))
           except ValueError:
               orders = orders.none()
       else:
           orders = orders.filter(
               Q(tenKhach__icontains=query) |  
               Q(ban__banso__icontains=query) |
               Q(ngay__icontains=query) |
               Q(ngay_thanh_toan__icontains=query) 
           )

    return render(request, 'rm/doanhthu.html', {
       'orders': orders,
       'query': query
    })

def order_detail_view(request, ban_id):
    """
    Xem chi tiết đơn hàng của bàn và cập nhật các món ăn trong đơn hàng
    
    Input:
        request 
        ban_id: ID của bàn cần xem chi tiết đơn hàng
    
    Output:
        Giao diện HTML hiển thị chi tiết đơn hàng của bàn, bao gồm các món ăn đã đặt và form để thêm món ăn mới
    """
    ban = get_object_or_404(Ban, id=ban_id)
    order = Order.objects.filter(ban=ban, tinhtrang=False).first()

    if not order:
        return redirect('ban_view')

    if request.method == "POST":
        form = AddMenuItemForm(request.POST)
        if form.is_valid():
            menu_item = form.cleaned_data['menu_item']
            soluong = form.cleaned_data['soluong']
            ChiTietOrder.objects.create(
                order=order,
                menu_item=menu_item,
                soluong=soluong,
                gia=menu_item.gia,
                tinhtrang='chua_len',
            )
            return redirect('order_detail', ban_id=ban_id)
    else:
        form = AddMenuItemForm()

    chi_tiet_order = order.items.all()
    order.save()

    return render(request, 'rm/order_detail.html', {
        'ban': ban,
        'order': order,
        'chi_tiet_order': chi_tiet_order,
        'form': form,
    })

def update_tinhtrang(request, chi_tiet_order_id):
    """
    Cập nhật trạng thái của một món ăn trong đơn hàng
    
    Input:
        request
        chi_tiet_order_id: ID của chi tiết đơn hàng cần cập nhật trạng thái
    
    Output:
        JSON phản hồi với thông báo về trạng thái cập nhật thành công hoặc lỗi
    """
    user = request.user
    nhanvien_trong_ca = LichLamViec.objects.filter(nhanvien=user, trangthai_nhanvien='trong_ca').exists()

    try:
        chi_tiet_order = ChiTietOrder.objects.get(id=chi_tiet_order_id)
    except ChiTietOrder.DoesNotExist:
        return JsonResponse({'error': 'Chi tiết order không tồn tại'}, status=404)

    if user.chucvu == 'bep' and chi_tiet_order.tinhtrang == 'chua_len' and nhanvien_trong_ca:
        chi_tiet_order.tinhtrang = 'da_len'
        chi_tiet_order.save()
        return JsonResponse({'success': 'Trạng thái đã cập nhật thành "Đã lên món"'})
    
    elif (user.chucvu == 'quanly' or user.chucvu == 'phucvu') and chi_tiet_order.tinhtrang == 'da_len':
        chi_tiet_order.tinhtrang = 'da_nhan'
        chi_tiet_order.save()
        return JsonResponse({'success': 'Trạng thái đã cập nhật thành "Đã nhận món"'})
    
    return JsonResponse({'error': 'Món đã được cập nhật trước đó'}, status=403)

def order_detail_dapaid(request, order_id):
    """
    Xem chi tiết đơn hàng đã thanh toán
    
    Input:
        request 
        order_id: ID của đơn hàng cần xem chi tiết
    
    Output:
        Giao diện HTML hiển thị chi tiết đơn hàng đã thanh toán, bao gồm thông tin bàn và các món ăn
    """
    order = get_object_or_404(Order, id=order_id)
    chi_tiet = order.items.all()
    ban = order.ban
    return render(request, 'rm/order_detail_dapaid.html', {
        'order': order, 
        'chi_tiet': chi_tiet,
        'ban': ban,
        })

def thanh_toan(request,order_id):
    """
    Thực hiện thanh toán cho một đơn hàng và cập nhật trạng thái của bàn và đơn hàng
    
    Input:
        request 
        order_id: ID của đơn hàng cần thanh toán    
    
    Output:
        Chuyển hướng về trang quản lý bàn nếu thanh toán thành công
        Hiển thị thông báo lỗi nếu có món ăn chưa được nhận và không thể thanh toán
    """
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)

        all_received = order.items.filter(tinhtrang='da_nhan').count() == order.items.count()

        if all_received:
            order.tinhtrang = True
            order.ngay_thanh_toan = timezone.now()
            ban = get_object_or_404(Ban, id=order.ban.id)
            ban.tinhtrangban = False
            ban.save()
            order.save()
            return redirect('ban_view')
        else:
            messages.error(request, 'Tất cả các món ăn chưa được nhận món! Không thể thanh toán')
            return redirect('order_detail', ban_id=order.ban.id)
        
def update_order_customer(request, order_id):
    """
    Cập nhật tên khách hàng
    
    Input:
        request
        order_id: ID của đơn hàng cần cập nhật tên khách hàng
    
    Output:
        Giao diện HTML hiển thị form để cập nhật tên khách hàng
    """
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()  
            return redirect('order_detail', ban_id=order.ban.id) 
    else:
        form = OrderUpdateForm(instance=order)
    
    return render(request, 'rm/update_order_customer.html', {'form': form, 'order': order})
# ----------------------------------------------------
@login_required
def calamviec(request):
    """
    Hiển thị lịch làm việc của nhân viên hoặc tất cả nhân viên (tùy theo quyền truy cập)
    
    Input:
        request 
    
    Output:
        Giao diện HTML hiển thị lịch làm việc của nhân viên hoặc tất cả nhân viên 
    """
    if request.user.chucvu in ['phucvu', 'bep']:  
        calamviec = LichLamViec.objects.filter(nhanvien=request.user).order_by('ngay', '-ca')
    else:
        calamviec = LichLamViec.objects.all().order_by('ngay', '-ca') 

    return render(request, 'rm/calamviec.html', {'calamviec': calamviec})

def them_ca_lam_viec(request):
    """
    Thêm ca làm việc cho nhân viên
    
    Input:
        request
    
    Output:
        Chuyển hướng về trang lịch làm việc sau khi ca làm việc được thêm thành công
    """
    if request.method == 'POST':
        form = LichLamViecForm(request.POST)
        if form.is_valid():
            form.save()  
            return redirect('calamviec') 

    else:
        form = LichLamViecForm()
    
    return render(request, 'rm/them_ca_lam_viec.html', {'form': form})

def sua_ca_lam_viec(request, pk):
    """
    Chỉnh sửa thông tin ca làm việc của nhân viên
    
    Input:
        request 
        pk: ID của ca làm việc cần chỉnh sửa
    
    Output:
        Chuyển hướng về trang lịch làm việc nếu ca làm việc được cập nhật thành công
    """
    ca = LichLamViec.objects.get(pk=pk)
    if request.method == 'POST':
        form = LichLamViecForm(request.POST, instance=ca)
        if form.is_valid():
            form.save()
            return redirect('calamviec')
    else:
        form = LichLamViecForm(instance=ca)
    
    return render(request, 'rm/sua_ca_lam_viec.html', {'form': form, 'ca': ca})

def xoa_ca_lam_viec(request, pk):
    """
    Xóa ca làm việc khỏi lịch làm việc
    
    Input:
        request 
        pk: ID của ca làm việc cần xóa
    
    Output:
        Chuyển hướng về trang lịch làm việc sau khi ca làm việc được xóa
    """
    ca = get_object_or_404(LichLamViec, pk=pk)
    if request.method == 'POST':
        ca.delete()
        return redirect('calamviec')
    
    return render(request, 'rm/xoa_ca_lam_viec.html', {'ca': ca})

def cham_cong_vao(request, id):
    """
    Chấm công vào khi nhân viên bắt đầu ca làm việc
    
    Input:
        id: ID của ca làm việc cần chấm công vào
    
    Output:
        Chuyển hướng về trang lịch làm việc sau khi nhân viên được chấm công vào
    """
    ca = get_object_or_404(LichLamViec, id=id)
    current_time = timezone.localtime(timezone.now())

    if ca.trangthai_nhanvien == 'chua_vaoca':
        ca.trangthai_nhanvien = 'trong_ca'
        ca.giovao = current_time
        ca.save()
    
    return redirect('calamviec')  

def cham_cong_ra(request, id):
    """
    Chấm công ra khi nhân viên kết thúc ca làm việc
    
    Input:
        id: ID của ca làm việc cần chấm công ra.
    
    Output:
        Chuyển hướng về trang lịch làm việc sau khi nhân viên được chấm công ra
    """
    ca = get_object_or_404(LichLamViec, id=id)
    current_time = timezone.localtime(timezone.now())

    if ca.trangthai_nhanvien == 'trong_ca':
        ca.trangthai_nhanvien = 'ra_ca'
        ca.giora = current_time
        ca.save()

    return redirect('calamviec')

def nhanvientrongca(request):
    """
    Hiển thị danh sách nhân viên hiện đang trong ca làm việc
    
    Input:
        request
    
    Output:
        Giao diện HTML hiển thị danh sách nhân viên đang làm việc
    """
    nhanvientrongca = LichLamViec.objects.filter(trangthai_nhanvien='trong_ca')

    return render(request, 'rm/nhanvientrongca.html', {'nvtrongca': nhanvientrongca})
