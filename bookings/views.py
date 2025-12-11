from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST 
# 👇 الاستيرادات (لم نغير شيئاً)
from .models import Service, Job, Notification, StationSettings, Attendance, WorkerProfile
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

# ========================================================
# 👇👇👇 الكود القديم (الأصلي) 👇👇👇
# ========================================================

def home(request):
    """ 
    واجهة الزبون (الموقع) - لم نلمسها
    """
    if request.method == 'POST':
        # 1. حفظ بيانات الحجز
        new_job = Job.objects.create( 
            client_name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            car_plate=request.POST.get('plate'),
            service_id=request.POST.get('service'),
            source='website',
            status='pending', 
            car_type="غير محدد",
            custom_desc=request.POST.get('description'), 
            voice_audio=request.FILES.get('voice_note') 
        )

        # 2. تحديد نوع الإشعار
        if request.FILES.get('voice_note'):
            notif_msg = f"🎙️ رسالة صوتية من {new_job.client_name}"
            n_type = 'voice'
        elif request.POST.get('description'):
            notif_msg = f"📝 طلب خاص من {new_job.client_name}"
            n_type = 'voice'
        else:
            notif_msg = f"🚗 حجز جديد: {new_job.client_name}"
            n_type = 'standard'

        # 3. منع التكرار
        existing_notif = Notification.objects.filter(job=new_job).first()
        if existing_notif:
            existing_notif.message = notif_msg
            existing_notif.notif_type = n_type
            existing_notif.is_read = False
            existing_notif.save()
        else:
            Notification.objects.create(
                job=new_job,
                message=notif_msg,
                notif_type=n_type
            )

        return render(request, 'home.html', {'success': True})

    services = Service.objects.all()
    return render(request, 'home.html', {'services': services})

# ========================================================
# 🚀 تحديث هام هنا: دالة الكاشير لتستقبل البيانات الجديدة
# ========================================================
@staff_member_required
def pos_dashboard(request):
    """ 
    نقطة البيع (KASHIR):
    تم تحديثها لحفظ (اسم العميل، الهاتف، نوع السيارة، الملاحظات)
    """
    if request.method == 'POST':
        try:
            # البيانات الأساسية القديمة
            service_id = request.POST.get('service')
            worker_id = request.POST.get('worker')
            plate = request.POST.get('plate') or "بدون لوحة"
            
            # 👇 البيانات الجديدة من التصميم "الخرافي"
            c_name = request.POST.get('client_name') or "زبون ورشة"
            c_phone = request.POST.get('phone') or ""
            c_type = request.POST.get('car_type') or "سيارة سياحية"
            notes = request.POST.get('notes') or ""

            # الحفظ في قاعدة البيانات
            Job.objects.create(
                client_name=c_name,   # جديد
                phone=c_phone,        # جديد
                car_plate=plate,
                car_type=c_type,      # جديد
                service_id=service_id,
                worker_id=worker_id,
                custom_desc=notes,    # جديد (الملاحظات)
                source='manual',
                status='processing'
            )
            messages.success(request, f"✅ تم تسجيل {c_type} ({plate}) بنجاح!")
        except Exception as e:
            messages.error(request, "❌ حدث خطأ أثناء التسجيل، تأكد من اختيار الخدمة والعامل.")
            print(f"Error: {e}")
            
    return redirect('/admin/bookings/job/')

@staff_member_required
def finish_wash(request, job_id):
    """ زر إنهاء الغسيل - لم نلمسها """
    try:
        job = Job.objects.get(id=job_id)
        if job.status != 'completed':
            job.status = 'completed' 
            job.save()
            messages.success(request, f"🏁 تم إنهاء غسيل السيارة {job.car_plate} بنجاح!")
    except Job.DoesNotExist:
        messages.error(request, "⚠️ هذه العملية غير موجودة.")
        pass 
    
    return redirect('/admin/bookings/job/')

# ========================================================
# 🔔 دوال الإشعارات - لم نلمسها
# ========================================================

@staff_member_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    Notification.objects.filter(job=job, is_read=False).update(is_read=True)
    return render(request, 'job_detail.html', {'job': job})

@staff_member_required
def get_notifications(request):
    count = Notification.objects.filter(is_read=False).count()
    latest = Notification.objects.filter(is_read=False)[:5].values('id', 'message', 'created_at', 'notif_type')
    return JsonResponse({'count': count, 'notifications': list(latest)})

@staff_member_required
def mark_read_and_redirect(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    notif.is_read = True
    notif.save()
    
    if notif.job_id and Job.objects.filter(id=notif.job_id).exists():
        return redirect('job_detail', job_id=notif.job_id)
    else:
        notif.delete()
        messages.warning(request, "⚠️ عذراً، هذا الحجز تم حذفه مسبقاً.")
        return redirect('/admin/bookings/job/')

# =========================================================
# 👇👇👇 الدوال الإدارية (تبديل الوضع + الحضور + الرواتب) 👇👇👇
# =========================================================

@staff_member_required
def toggle_mode(request):
    """ زر التبديل بين الرواتب والعمولة """
    if request.method == "POST":
        s, _ = StationSettings.objects.get_or_create(id=1)
        if s.current_mode == 'commission':
            s.current_mode = 'salary'
        else:
            s.current_mode = 'commission'
        s.save()
    return redirect('/admin/bookings/job/')

@staff_member_required
def update_attendance_manual(request):
    """ زر تسجيل الحضور """
    if request.method == "POST":
        w_id = request.POST.get('worker_id')
        worker = get_object_or_404(User, id=w_id)
        today = timezone.now().date()
        
        att, created = Attendance.objects.get_or_create(worker=worker, date=today)
        att.is_present = not att.is_present
        
        if hasattr(worker, 'profile'):
            att.day_salary_snapshot = worker.profile.daily_salary
            
        att.save()
        
    return redirect('/admin/bookings/job/')

@staff_member_required
@require_POST
def update_worker_salary_manual(request):
    """ 
    💰 دالة لحفظ الراتب اليومي للعامل
    هذه الدالة هي التي تصلح الخطأ السابق (NoReverseMatch)
    """
    worker_id = request.POST.get('worker_id')
    new_salary = request.POST.get('salary')
    
    if worker_id and new_salary:
        try:
            worker_user = get_object_or_404(User, id=worker_id)
            # تحديث أو إنشاء البروفايل
            profile, created = WorkerProfile.objects.get_or_create(user=worker_user)
            
            profile.daily_salary = float(new_salary)
            profile.save()
            
            messages.success(request, f"💰 تم تحديث راتب {worker_user.first_name} إلى {new_salary} د.ج")
        except Exception as e:
            messages.error(request, "❌ حدث خطأ أثناء تحديث الراتب.")
            print(f"Salary Update Error: {e}")
            
    return redirect('/admin/bookings/job/')