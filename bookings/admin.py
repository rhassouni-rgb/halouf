import json
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.db.models import Sum, Q
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import path
from django.utils.safestring import mark_safe # لإظهار الأزرار

# استيراد كافة الجداول
from .models import Service, Job, Booking, Advance, Notification, StationSettings, WorkerProfile, Attendance

# =========================================================
# ⚙️ إعدادات العناوين
# =========================================================
admin.site.unregister(Group)
admin.site.site_header = "نظام TurboWash المتكامل 🚿"
admin.site.index_title = "لوحة القيادة"

# =========================================================
# 1. إعدادات النظام
# =========================================================
@admin.register(StationSettings)
class StationSettingsAdmin(admin.ModelAdmin):
    list_display = ('current_mode', 'updated_at')
    def has_add_permission(self, request):
        return not StationSettings.objects.exists()

# =========================================================
# 2. إدارة الخدمات
# =========================================================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'worker_commission', 'icon')
    list_editable = ('price', 'worker_commission', 'icon')
    ordering = ('name',)

# =========================================================
# 3. سجل العمليات (JobAdmin)
# =========================================================
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    # ---------------------------------------------------------
    # تخصيص واجهة الإدارة (List Display)
    # ---------------------------------------------------------
    fieldsets = (
        ('👤 بيانات الزبون', {'fields': (('client_name', 'phone'), ('car_plate', 'car_type'))}),
        ('🧼 تفاصيل الخدمة', {'fields': ('service', 'worker', 'status', 'source')}),
        ('💰 الحسابات والوقت', {'fields': (('final_price', 'final_commission'), 'created_at')}),
        ('🎙️ تفاصيل الطلب الخاص', {'fields': ('voice_audio', 'custom_desc')}),
    )
    
    # إضافة 'actions_column' لعرض الأزرار
    list_display = ('car_plate', 'status', 'service', 'worker', 'created_at', 'final_price', 'final_commission', 'net_profit_display', 'actions_column')
    
    # السماح بتعديل الحالة والعامل مباشرة في الجدول (وهذا هو سبب طلب زر الحفظ)
    list_editable = ('status', 'worker',) 
    
    list_filter = ('status', 'worker', 'service', 'created_at') 
    search_fields = ('car_plate', 'client_name', 'worker__username')
    ordering = ('-created_at',)
    readonly_fields = ('final_price', 'final_commission', 'created_at') 

    # ---------------------------------------------------------
    # 🔥 (إضافة مهمة جداً) فلترة الجدول لفصل النظامين بصرياً 🔥
    # ---------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        try:
            # نجلب النظام الحالي
            settings = StationSettings.objects.first()
            current_mode = settings.current_mode if settings else 'commission'
        except:
            current_mode = 'commission'

        # إذا كنا في الرواتب، اعرض فقط عمليات الرواتب
        if current_mode == 'salary':
            return qs.filter(system_mode='salary')
        
        # إذا كنا في العمولة، اعرض فقط عمليات العمولة
        return qs.filter(system_mode='commission')

    # ---------------------------------------------------------
    # وظائف الحساب
    # ---------------------------------------------------------
    def net_profit_display(self, obj):
        profit = (obj.final_price or 0) - (obj.final_commission or 0)
        return format_html('<span style="color: green;">+{} DA</span>', profit)
    net_profit_display.short_description = "💰 الربح"

    # ---------------------------------------------------------
    # إزالة التعديل الذي يسمح بحقول فارغة (لضمان الإلزامية)
    # ---------------------------------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "worker":
            kwargs["queryset"] = User.objects.filter(is_staff=True)
        
        # ❌ تمت إزالة هذا الكود الذي يلغي إلزامية الحقل: 
        # if db_field.name == "service":
        #     kwargs["required"] = False 

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # ---------------------------------------------------------
    # ⚙️ إضافة مسارات URL مخصصة للأزرار
    # ---------------------------------------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # مسار لمعالجة الإجراءات الفردية (حفظ أو حذف)
            path('<int:job_id>/action/', self.admin_site.admin_view(self.response_action), name='job_action'),
        ]
        return custom_urls + urls

    # ---------------------------------------------------------
    # 🔗 عمود الأزرار (actions_column)
    # ---------------------------------------------------------
    def actions_column(self, obj):
        """عرض أزرار الحفظ والحذف لكل عملية."""
        save_link = self.save_job_link(obj)
        delete_link = self.delete_job_link(obj)
        return format_html('{} {}', save_link, delete_link)
        
    actions_column.short_description = format_html('الإجراءات')
    actions_column.allow_tags = True
    
    def save_job_link(self, obj):
        """زر الحفظ الفردي"""
        # نستخدم Django Admin URL لـ Job Admin
        url = self.admin_site.name
        # الرابط يشير إلى URL المخصص job_action
        link = f"/{url}/bookings/job/{obj.pk}/action/?type=save" 
        return mark_safe(f'<a href="{link}" class="button" style="background-color: #4CAF50; color: white; padding: 5px 10px; margin-right: 5px; border-radius: 3px;" title="حفظ التغييرات في هذا الصف">💾 حفظ</a>')

    def delete_job_link(self, obj):
        """زر الحذف الفردي"""
        url = self.admin_site.name
        link = f"/{url}/bookings/job/{obj.pk}/action/?type=delete"
        # نحتاج تأكيد جافاسكريبت للحذف
        return mark_safe(f'<a href="{link}" class="button" onclick="return confirm(\'هل أنت متأكد من حذف هذه العملية؟\')" style="background-color: #f44336; color: white; padding: 5px 10px; border-radius: 3px;" title="حذف العملية">🗑️ حذف</a>')
    
    # ---------------------------------------------------------
    # ⚡ دالة معالجة الأزرار المخصصة (Response Action)
    # ---------------------------------------------------------
    def response_action(self, request, job_id):
        job = self.get_object(request, job_id)
        if not job:
            messages.error(request, "لم يتم العثور على العملية.")
            return redirect('../')

        action_type = request.GET.get('type')
        
        if action_type == 'save':
            # عند ضغط زر الحفظ، يتم تنفيذ Job.save()
            # هذا يضمن إعادة حساب العمولة إذا تغيرت الحالة إلى 'completed'
            try:
                job.save() 
                messages.success(request, f"✅ تم حفظ التغييرات بنجاح للعملية {job.pk}.")
            except Exception as e:
                messages.error(request, f"خطأ أثناء الحفظ: {e}")
            
        elif action_type == 'delete':
            # عند ضغط زر الحذف
            job.delete()
            messages.success(request, f"🗑️ تم حذف العملية {job.pk} بنجاح.")

        # إعادة التوجيه إلى صفحة القائمة بعد الإجراء
        return redirect('../')

    # ---------------------------------------------------------
    # 🔥 دالة الفصل التام بين النظامين (Changelist View)
    # ---------------------------------------------------------
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # ⚡ معالجة الحفظ السريع (Quick Add)
        if request.method == "POST" and 'quick_add' in request.POST:
            try:
                srv_id = request.POST.get('service')
                worker_id = request.POST.get('worker') # 🛑 إضافة التحقق من العامل هنا
                
                # 🛑 التحقق من الإلزامية: الخدمة والعامل
                if not srv_id or not worker_id:
                    error_msg = "⚠️ يجب اختيار كل من **الخدمة** و **العامل** لتسجيل عملية الكاشير!"
                    self.message_user(request, error_msg, level=messages.ERROR)
                    return redirect(request.get_full_path())

                selected_service = Service.objects.get(id=srv_id)
                
                commission_value = 0
                settings_obj, _ = StationSettings.objects.get_or_create(id=1)
                if settings_obj.current_mode != 'salary':
                    commission_value = selected_service.worker_commission

                # ✅ المعالجة الأمنية للقيم الفارغة المسموح بها في DB
                input_phone = request.POST.get('phone') or "-"
                input_name = request.POST.get('client_name') or "زبون مباشر"
                input_car_type = request.POST.get('car_type') or "غير محدد"

                new_job = Job(
                    source='manual', 
                    car_plate=request.POST.get('plate') or "بدون لوحة",
                    
                    car_type=input_car_type,
                    client_name=input_name,
                    phone=input_phone,
                    
                    worker_id=worker_id, # استخدام worker_id
                    status='processing', # تغيير الحالة الافتراضية إلى 'processing' عند التسجيل الفوري
                    
                    service=selected_service,
                    # لا نحتاج لتعيين final_price/commission هنا، دالة save في models.py ستحسبها عند الحفظ الأول
                )
                
                # عند الحفظ، سيتم حساب final_price و final_commission (إذا كانت الحالة completed)
                new_job.save() 
                self.message_user(request, "✅ تم تسجيل العملية بنجاح", level=messages.SUCCESS)
                return redirect(request.get_full_path())
            except Exception as e:
                # عرض رسالة خطأ أكثر وضوحاً
                self.message_user(request, f"❌ حدث خطأ غير متوقع: {e}", level=messages.ERROR)
                return redirect(request.get_full_path())

        # ... (بقية منطق changelist_view لنظام الرواتب والعمولات) ...
        extra_context = extra_context or {}
        
        # 1. بيانات مشتركة
        extra_context['services'] = Service.objects.all()
        extra_context['workers'] = User.objects.filter(is_staff=True)

        # 2. تحديد الوضع الحالي
        settings_obj, _ = StationSettings.objects.get_or_create(id=1)
        current_mode = settings_obj.current_mode
        
        today = timezone.now().date()
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # =========================================================
        # 🔴 المسار الأول: نظام الرواتب (SALARY MODE)
        # =========================================================
        if current_mode == 'salary':
            self.change_list_template = "admin/bookings/job/salary_dashboard.html"
            
            workers_list = []
            total_salaries_today = 0
            
            for w in extra_context['workers']:
                profile, _ = WorkerProfile.objects.get_or_create(user=w)
                daily_wage = profile.daily_salary
                att = Attendance.objects.filter(worker=w, date=today).first()
                is_present = att.is_present if att else False
                
                if is_present: total_salaries_today += daily_wage
                workers_list.append({'worker': w, 'salary': daily_wage, 'is_present': is_present})

            # ✅ فلترة الحسابات حسب النظام + استثناء الملغاة (canceled)
            total_revenue = Job.objects.filter(
                created_at__range=(today_start, today_end),
                system_mode='salary'  # ⬅️ الفلترة المضافة
            ).exclude(status='canceled').aggregate(Sum('final_price'))['final_price__sum'] or 0

            extra_context.update({
                'workers_list': workers_list,
                'salary_stats': {
                    'total_revenue': total_revenue,
                    'total_salaries': total_salaries_today,
                    'net_profit': total_revenue - total_salaries_today
                },
                'latest_jobs': Job.objects.filter(
                    created_at__range=(today_start, today_end), 
                    system_mode='salary'
                ).exclude(status='canceled').order_by('-created_at')[:10]
            })

        # =========================================================
        # 🔵 المسار الثاني: نظام العمولات (COMMISSION MODE)
        # =========================================================
        else:
            self.change_list_template = "admin/bookings/job/change_list_jazzmin.html"
            
            # ✅ فلترة الحسابات حسب النظام + استثناء الملغاة
            today_jobs = Job.objects.filter(
                created_at__range=(today_start, today_end), 
                system_mode='commission'  # ⬅️ الفلترة المضافة
            )
            active_jobs = today_jobs.exclude(status='canceled')
            
            total_revenue = active_jobs.aggregate(Sum('final_price'))['final_price__sum'] or 0
            total_commission = active_jobs.aggregate(Sum('final_commission'))['final_commission__sum'] or 0
            net_profit = total_revenue - total_commission
            pending_jobs = today_jobs.filter(status='processing').count()

            # ✅ استثناء الملغاة من الشهر
            month_jobs = Job.objects.filter(
                created_at__month=now.month, 
                created_at__year=now.year,
                system_mode='commission'
            ).exclude(status='canceled')
            profit_month = (month_jobs.aggregate(Sum('final_price'))['final_price__sum'] or 0) - (month_jobs.aggregate(Sum('final_commission'))['final_commission__sum'] or 0)

            # ✅ استثناء الملغاة من السنة
            year_jobs = Job.objects.filter(
                created_at__year=now.year,
                system_mode='commission'
            ).exclude(status='canceled')
            profit_year = (year_jobs.aggregate(Sum('final_price'))['final_price__sum'] or 0) - (year_jobs.aggregate(Sum('final_commission'))['final_commission__sum'] or 0)

            last_7_days = now - timedelta(days=6)
            
            # ✅ استثناء الملغاة من المبيان
            chart_data = Job.objects.filter(
                created_at__gte=last_7_days,
                system_mode='commission'
            ).exclude(status='canceled').annotate(day=TruncDay('created_at')).values('day').annotate(rev=Sum('final_price'), comm=Sum('final_commission')).order_by('day')

            dates, profits, revenues = [], [], []
            data_dict = {item['day'].date(): item for item in chart_data}
            for i in range(7):
                d = (last_7_days + timedelta(days=i)).date()
                dates.append(d.strftime('%Y-%m-%d'))
                val = data_dict.get(d, {'rev': 0, 'comm': 0})
                revenues.append(val['rev'] or 0)
                profits.append((val['rev'] or 0) - (val['comm'] or 0))

            extra_context.update({
                'stats': {
                    'total_revenue': total_revenue, 
                    'total_commission': total_commission, 
                    'profit': net_profit,
                    'profit_month': profit_month, 
                    'profit_year': profit_year, 
                    'pending_jobs': pending_jobs,
                    'chart_dates': json.dumps(dates, cls=DjangoJSONEncoder),
                    'chart_profits': json.dumps(profits, cls=DjangoJSONEncoder),
                    'chart_revenues': json.dumps(revenues, cls=DjangoJSONEncoder),
                }
            })

        return super().changelist_view(request, extra_context=extra_context)

# =========================================================
# 4. المصروفات والإشعارات والحضور
# =========================================================
@admin.register(Advance)
class AdvanceAdmin(admin.ModelAdmin):
    list_display = ('worker', 'amount', 'date', 'note')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'is_read', 'created_at')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('worker', 'date', 'is_present', 'day_salary_snapshot')
    list_filter = ('date', 'worker')

# =========================================================
# 5. تقرير الرواتب الذكي (Payroll)
# =========================================================
class Payroll(User):
    class Meta: proxy = True; verbose_name = '💰 تقرير الرواتب'; verbose_name_plural = '💰 تقارير الرواتب'

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('get_full_name_custom', 'get_salary_mode', 'month_earnings', 'month_advances', 'net_salary')
    def has_add_permission(self, request): return False

    def get_full_name_custom(self, obj): return obj.first_name or obj.username
    get_full_name_custom.short_description = "العامل"

    def get_salary_mode(self, obj):
        setting = StationSettings.objects.first()
        mode = setting.current_mode if setting else 'commission'
        return "راتب يومي" if mode == 'salary' else "نسبة"
    get_salary_mode.short_description = "نظام الحساب"

    def month_earnings(self, obj):
        setting = StationSettings.objects.first()
        mode = setting.current_mode if setting else 'commission'
        start_month = timezone.now().replace(day=1)

        if mode == 'salary':
            total = Attendance.objects.filter(worker=obj, date__gte=start_month, is_present=True).aggregate(Sum('day_salary_snapshot'))['day_salary_snapshot__sum'] or 0
            days = Attendance.objects.filter(worker=obj, date__gte=start_month, is_present=True).count()
            return format_html('<span style="color:blue;">{} د.ج ({} أيام)</span>', total, days)
        else:
            # ✅ استثناء الملغاة وفلترة نظام العمولة
            total = Job.objects.filter(
                worker=obj, 
                created_at__gte=start_month, 
                status='completed',
                system_mode='commission'
            ).exclude(status='canceled').aggregate(Sum('final_commission'))['final_commission__sum'] or 0
            return format_html('<span style="color:blue;">{} د.ج (نسبة)</span>', total)
    month_earnings.short_description = "الاستحقاق"

    def month_advances(self, obj):
        start_month = timezone.now().replace(day=1)
        total = Advance.objects.filter(worker=obj, date__gte=start_month).aggregate(Sum('amount'))['amount__sum'] or 0
        return format_html('<span style="color:red;">- {} د.ج</span>', total)
    month_advances.short_description = "المسحوبات"

    def net_salary(self, obj):
        start_month = timezone.now().replace(day=1)
        setting = StationSettings.objects.first()
        mode = setting.current_mode if setting else 'commission'

        if mode == 'salary':
            earned = Attendance.objects.filter(worker=obj, date__gte=start_month, is_present=True).aggregate(Sum('day_salary_snapshot'))['day_salary_snapshot__sum'] or 0
        else:
            # ✅ استثناء الملغاة وفلترة نظام العمولة في الصافي
            earned = Job.objects.filter(
                worker=obj, 
                created_at__gte=start_month, 
                status='completed',
                system_mode='commission'
            ).exclude(status='canceled').aggregate(Sum('final_commission'))['final_commission__sum'] or 0
        
        taken = Advance.objects.filter(worker=obj, date__gte=start_month).aggregate(Sum('amount'))['amount__sum'] or 0
        net = earned - taken
        color = "green" if net >= 0 else "red"
        return format_html('<b style="color:{}; background:#e8f5e9; padding:5px;">= {} د.ج</b>', color, net)
    net_salary.short_description = "✅ الصافي"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

# =========================================================
# 6. إدارة العمال
# =========================================================
try: admin.site.unregister(User)
except: pass

class WorkerProfileInline(admin.StackedInline):
    model = WorkerProfile
    can_delete = False
    verbose_name_plural = '💰 الراتب اليومي'

class WorkerProxy(User):
    class Meta: proxy = True; verbose_name = "إضافة عامل"; verbose_name_plural = "3. فريق العمل 👷"

@admin.register(WorkerProxy)
class WorkerAdmin(admin.ModelAdmin):
    inlines = (WorkerProfileInline,)
    fields = ('username', 'first_name', 'password', 'is_active')
    list_display = ('username', 'first_name', 'get_salary', 'is_active')
    
    def get_salary(self, obj):
        if hasattr(obj, 'profile'): return f"{obj.profile.daily_salary} DA"
        return "-"
    get_salary.short_description = "الراتب"

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        if 'password' in form.changed_data: obj.set_password(obj.password)
        obj.save()