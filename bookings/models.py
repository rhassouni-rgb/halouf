from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ----------------------------------------------------
# 📌 خيارات الموديلز (Choices)
# ----------------------------------------------------

# تعريف خيارات الحالة 
STATUS_CHOICES = [
    ('pending', '⏳ قيد الانتظار'), 
    ('processing', '🧼 جاري العمل'), 
    ('completed', '✅ مكتملة'),
    ('canceled', '❌ ملغاة'),
]

# تعريف خيارات المصدر
SOURCE_CHOICES = [
    ('website', '🌍 حجز من الموقع'),
    ('manual', '👋 زبون مباشر (كاشير)'),
]

# تعريف أنواع الإشعارات
NOTIF_TYPE_CHOICES = [
    ('standard', '🔔 حجز عادي'),
    ('voice', '🎙️ رسالة صوتية'),
]

# ----------------------------------------------------
# 1. قائمة الخدمات والأسعار (Service)
# ----------------------------------------------------
class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="نوع الغسيل")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="سعر الزبون")
    worker_commission = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="أجر العامل")
    icon = models.CharField(max_length=50, default='🚗', verbose_name="أيقونة الخدمة")

    def __str__(self):
        return f"{self.name} ({self.price} د.ج)"
    
    class Meta:
        verbose_name = "خدمة"
        verbose_name_plural = "1. قائمة الخدمات 📋"

# ----------------------------------------------------
# 2. سجل العمليات الأساسي (Job)
# ----------------------------------------------------
class Job(models.Model): 
    
    # بيانات الزبون
    client_name = models.CharField(max_length=100, default='زبون مباشر', verbose_name="اسم الزبون")
    phone = models.CharField(max_length=15, default='-', verbose_name="رقم الهاتف")
    car_plate = models.CharField(max_length=20, default='بدون لوحة', verbose_name="لوحة السيارة")

    # بيانات الطلب
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual', verbose_name="المصدر")
    car_type = models.CharField(max_length=50, default='غير محدد', verbose_name="نوع السيارة")
    
    # الخدمة: مطلوبة
    service = models.ForeignKey(
        Service, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="الخدمة"
    )
    
    # الطلبات الخاصة
    voice_audio = models.FileField(upload_to='voice_notes/%Y/%m/', blank=True, null=True, verbose_name="تسجيل صوتي 🎙️")
    custom_desc = models.TextField(blank=True, null=True, verbose_name="وصف المشكلة/الطلب")
    
    # العامل: مطلوب
    worker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'is_staff': True}, 
        verbose_name="👨‍🔧 العامل المنفذ"
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='processing', verbose_name="الحالة")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="وقت التسجيل")

    # الحسابات المالية
    final_price = models.DecimalField(max_digits=8, decimal_places=2, editable=False, default=0, verbose_name="السعر النهائي")
    final_commission = models.DecimalField(max_digits=8, decimal_places=2, editable=False, default=0, verbose_name="عمولة العامل")
    
    # 🆕 حقل جديد: لتحديد النظام الذي سُجلت فيه العملية (راتب أم عمولة) لفصلهما تماماً
    system_mode = models.CharField(max_length=20, default='commission', editable=False, verbose_name="نظام العملية")

    # دوال مساعدة لضمان عدم وجود أخطاء
    def get_final_price(self):
        """يحسب السعر النهائي، يرجع 0 في حالة عدم وجود خدمة."""
        return self.service.price if self.service else 0

    def get_commission(self):
        """
        يحسب العمولة بناءً على الخدمة.
        لكن الحساب يعتمد على 'system_mode' الخاص بهذه العملية تحديداً.
        """
        # إذا كان نظام العملية المسجل هو 'commission'، نحسب العمولة
        if self.system_mode == 'commission':
            return self.service.worker_commission if self.service else 0
        
        # إذا كان النظام 'salary' أو غير ذلك، العمولة صفر
        return 0

    def save(self, *args, **kwargs):
        is_new_record = not self.pk
        
        # 1. عند الإنشاء فقط: نحدد السعر ونختم العملية بنظام العمل الحالي
        if is_new_record:
            self.final_price = self.get_final_price()
            try:
                # جلب النظام الحالي من الإعدادات وحفظه في العملية
                settings = StationSettings.objects.first()
                self.system_mode = settings.current_mode if settings else 'commission'
            except:
                self.system_mode = 'commission'

        # 2. منطق حساب العمولة (يحدث عند كل تعديل)
        
        # إذا كانت الحالة "ملغاة" (canceled) أو غير مكتملة -> تصفير العمولة
        if self.status == 'canceled' or self.status != 'completed':
            self.final_commission = 0
            
        # إذا كانت الحالة "مكتملة" -> نحسب العمولة بناءً على system_mode
        elif self.status == 'completed':
            self.final_commission = self.get_commission()
            
        super().save(*args, **kwargs)

    def __str__(self):
        service_name = self.service.name if self.service else 'بدون خدمة'
        return f"{self.car_plate} - {service_name} ({self.status})"

    class Meta:
        verbose_name = "عملية"
        verbose_name_plural = "2. سجل العمليات (الكاشير) 🚘"

# ----------------------------------------------------
# 3. نموذج وهمي للحجوزات (Booking) - Proxy Model
# ----------------------------------------------------
class Booking(Job):
    """يستخدم لفصل عرض حجوزات الموقع عن عمليات الكاشير."""
    class Meta:
        proxy = True
        verbose_name = "محجوزة قادمة"
        verbose_name_plural = "3. المحجوزات (الطلبات من الموقع) 🗓️"

# ----------------------------------------------------
# 4. جدول المصروفات (Advance)
# ----------------------------------------------------
class Advance(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True}, verbose_name="العامل")
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="قيمة المصروف (د.ج)")
    date = models.DateTimeField(default=timezone.now, verbose_name="التاريخ")
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name="ملاحظة / سبب")

    def __str__(self):
        return f"{self.worker} - {self.amount}"

    class Meta:
        verbose_name = "خصم / سلفة"
        verbose_name_plural = "4. سجل المصروفات والسلف 💸"

# ----------------------------------------------------
# 5. جدول الإشعارات (Notification)
# ----------------------------------------------------
class Notification(models.Model):
    job = models.ForeignKey(
        Job, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="العملية المرتبطة"
    )
    message = models.CharField(max_length=255, verbose_name="نص الإشعار")
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES, default='standard', verbose_name="نوع التنبيه")
    is_read = models.BooleanField(default=False, verbose_name="تمت القراءة؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإشعار")

    class Meta:
        ordering = ['-created_at'] # الأحدث يظهر أولاً
        verbose_name = "إشعار"
        verbose_name_plural = "5. سجل التنبيهات 🔔"

    def __str__(self):
        return self.message

# =========================================================
# 👇👇👇 الإضافات الخاصة بنظام الرواتب الثابتة (Mode 2) 👇👇👇
# =========================================================

# 6. إعدادات النظام (StationSettings)
class StationSettings(models.Model):
    MODE_CHOICES = [
        ('commission', '📊 نظام العمولة (Mode 1)'),
        ('salary', '💼 نظام الرواتب الثابتة (Mode 2)'),
    ]
    current_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='commission', verbose_name="نظام العمل")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    def __str__(self):
        return f"الوضع الحالي: {self.get_current_mode_display()}"

    class Meta:
        verbose_name = "⚙️ إعدادات النظام"
        verbose_name_plural = "⚙️ إعدادات النظام (التبديل)"

# 7. ملف العامل (WorkerProfile)
class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="العامل")
    daily_salary = models.DecimalField(max_digits=8, decimal_places=2, default=1000.00, verbose_name="الراتب اليومي (د.ج)")

    def __str__(self):
        return f"{self.user.username} ({self.daily_salary} د.ج)"

    class Meta:
        verbose_name = "راتب عامل"
        verbose_name_plural = "👤 رواتب العمال اليومية"

# 8. سجل الحضور (Attendance)
class Attendance(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="العامل")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    is_present = models.BooleanField(default=False, verbose_name="حاضر؟")
    
    # نحفظ قيمة الراتب في ذلك اليوم (snapshot)
    day_salary_snapshot = models.DecimalField(max_digits=8, decimal_places=2, default=0, editable=False)

    def save(self, *args, **kwargs):
        # 1. جلب الراتب الحالي وتخزينه كـ Snapshot
        if self.is_present and hasattr(self.worker, 'profile'):
            # يتم التخزين فقط في حال إنشاء السجل أو كانت القيمة الافتراضية 0
            if self.day_salary_snapshot == 0: 
                self.day_salary_snapshot = self.worker.profile.daily_salary
        
        # 2. تصفير الراتب إذا كان العامل غائباً
        if not self.is_present:
            self.day_salary_snapshot = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker} - {self.date}"

    class Meta:
        unique_together = ('worker', 'date') # يمنع تسجيل حضور مرتين في نفس اليوم
        verbose_name = "سجل حضور"
        verbose_name_plural = "📅 سجل الحضور والغياب"