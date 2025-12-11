"""
Django settings for core project.
LEGENDARY EDITION: Jazzmin Theme + Bilingual Support (AR/EN) + Full Configuration.
READY FOR PRODUCTION (DEPLOYMENT MODE)
"""

from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# 🔐 Security Settings
# =========================================================
SECRET_KEY = 'django-insecure-legendary-pro-key-turbowash'

# ⚠️ هام: اجعلها False عند الرفع على السيرفر الحقيقي للأمان
DEBUG = False

# السماح لجميع النطاقات (لضمان عمل الموقع فوراً)
ALLOWED_HOSTS = ['*']

# =========================================================
# 📦 Installed Apps
# =========================================================
INSTALLED_APPS = [
    # 1. مكتبة التصميم (يجب أن تكون في البداية)
    'jazzmin',

    # 👇 [إضافة جديدة] مكتبة الترجمة (يجب أن تكون قبل Admin)
    'modeltranslation',

    # 2. تطبيقات جانغو الأساسية
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 3. مكتبات مساعدة
    'django.contrib.humanize', # لتحسين عرض الأرقام

    # 4. تطبيقك
    'bookings',
]

# =========================================================
# ⚙️ Middleware
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # 👇 هذا السطر هو المسؤول عن تغيير اللغة (مهم جداً)
    'django.middleware.locale.LocaleMiddleware',
    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# =========================================================
# 📄 Templates
# =========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # مجلد القوالب العامة
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# =========================================================
# 🗄️ Database
# =========================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# =========================================================
# 🔑 Password Validation
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================================================
# 🌍 Internationalization (اللغات والوقت)
# =========================================================
LANGUAGE_CODE = 'ar' # اللغة الافتراضية للواجهة

TIME_ZONE = 'Africa/Algiers' # توقيت الجزائر

USE_I18N = True # تفعيل نظام الترجمة
USE_L10N = True # تفعيل تنسيق الأرقام المحلي
USE_TZ = True   # تفعيل التوقيت العالمي

# اللغات المتاحة في النظام
LANGUAGES = [
    ('ar', _('Arabic')),
    ('en', _('English')),
    ('fr', _('French')),
]

# مسار ملفات الترجمة
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# =========================================================
# 📂 Static & Media Files
# =========================================================
# رابط الملفات الثابتة (يجب أن يبدأ بـ /)
STATIC_URL = '/static/'

# المجلد الذي سيجمع فيه السيرفر كل ملفات التصميم (مهم جداً للنشر)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# المجلدات التي تحتوي على ملفاتك الخاصة أثناء التطوير
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# إعدادات رفع الصور (Media)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ضروري لعمل Jazzmin ونوافذه المنبثقة بشكل صحيح
X_FRAME_OPTIONS = 'SAMEORIGIN'

# =========================================================
# 🎤 Audio Upload Configuration
# =========================================================
# السماح برفع ملفات حتى 10 ميجابايت (للتسجيلات الصوتية الطويلة)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================================
# 🎨 JAZZMIN SETTINGS (إعدادات الواجهة الفخمة)
# =========================================================
JAZZMIN_SETTINGS = {
    # العناوين والشعار
    "site_title": "TurboWash Admin",
    "site_header": "نظام الإدارة المركزية",
    "site_brand": "TurboWash Pro",
    "welcome_sign": "مرحباً بك في لوحة القيادة",
    "copyright": "TurboWash Ltd",
    
    # البحث العام
    "search_model": "bookings.Job",

    # تفعيل زر تغيير اللغة
    "language_chooser": True,

    # الروابط العلوية
    "topmenu_links": [
        {"name": "الرئيسية", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "واجهة الزبون", "url": "home", "new_window": True},
        {"model": "auth.User"},
    ],

    # إعدادات القائمة الجانبية
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # أيقونات التطبيقات (FontAwesome)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "bookings.Service": "fas fa-list-alt",
        "bookings.Job": "fas fa-car-side",
        "bookings.Booking": "fas fa-globe",
        "bookings.Payroll": "fas fa-money-bill-wave",
        "bookings.WorkerProxy": "fas fa-hard-hat",
        "bookings.Advance": "fas fa-hand-holding-usd", # أيقونة المصروفات
    },

    # ترتيب القائمة الجانبية
    "order_with_respect_to": [
        "bookings.Job", 
        "bookings.Booking", 
        "bookings.Payroll", 
        "bookings.Advance",
        "bookings.Service", 
        "bookings.WorkerProxy",
        "auth"
    ],

    # واجهة تخصيص الألوان (نجعلها False في الإنتاج للنظافة، يمكنك إعادتها True إذا أردت)
    "show_ui_builder": False,
}

# =========================================================
# 🖌️ JAZZMIN UI TWEAKS (تخصيص الألوان الافتراضي)
# =========================================================
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-white",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary", # القائمة الجانبية داكنة
    "sidebar_nav_small_text": False,
    "theme": "flatly", # ثيم أنيق جداً (Flat Design)
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}