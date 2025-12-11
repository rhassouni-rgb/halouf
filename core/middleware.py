from django.shortcuts import render
from django.utils import timezone
import datetime

class TrialPeriodMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 👇 حدد تاريخ انتهاء التجربة هنا (مثلاً بعد أسبوع من اليوم)
        # سنة، شهر، يوم
        self.expiry_date = datetime.datetime(2025, 12, 12) 

    def __call__(self, request):
        # التحقق من التاريخ الحالي
        if timezone.now() > self.expiry_date.astimezone():
            # إذا انتهت المدة، اظهر صفحة التنبيه فقط
            return render(request, 'trial_expired.html')

        response = self.get_response(request)
        return response