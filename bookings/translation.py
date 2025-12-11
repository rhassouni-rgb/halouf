from modeltranslation.translator import register, TranslationOptions
from .models import Service

# هنا نخبر النظام أننا نريد ترجمة حقل "الاسم" في جدول الخدمات
@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ('name',)