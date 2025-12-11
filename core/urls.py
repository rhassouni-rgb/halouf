from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns 
from django.conf import settings
from django.conf.urls.static import static

# 👇 تأكد من استيراد كل الدوال (بما فيها دالة الراتب الجديدة)
from bookings.views import (
    home, 
    pos_dashboard, 
    finish_wash, 
    get_notifications, 
    mark_read_and_redirect, 
    job_detail,
    toggle_mode,              
    update_attendance_manual,
    update_worker_salary_manual  # 🆕 هام جداً: أضفنا استيراد دالة الراتب
)

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    # لوحة تحكم الأدمن
    path('admin/', admin.site.urls),
    
    # الصفحة الرئيسية
    path('', home, name='home'),
    
    # الكاشير
    path('pos/', pos_dashboard, name='pos_dashboard'),
    
    # إنهاء الغسيل
    path('finish/<int:job_id>/', finish_wash, name='finish_wash'),
    
    # صفحة التفاصيل
    path('job/<int:job_id>/', job_detail, name='job_detail'),

    # الإشعارات
    path('api/notifications/', get_notifications, name='get_notifications'),
    path('notifications/read/<int:notif_id>/', mark_read_and_redirect, name='mark_notification_read'),
    
    # =========================================================
    # 👇👇👇 الروابط الإدارية (تم إضافة رابط الراتب المفقود) 👇👇👇
    # =========================================================
    path('api/toggle-mode/', toggle_mode, name='toggle_mode'),
    path('api/attendance/', update_attendance_manual, name='update_attendance_manual'),
    
    # ✅ هذا هو السطر الذي كان ينقصك ويسبب الخطأ 500
    path('api/update-salary/', update_worker_salary_manual, name='update_worker_salary_manual'),
    
    prefix_default_language=False 
)

# تشغيل الميديا
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)