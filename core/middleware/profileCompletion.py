from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class ProfileCompletionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and \
           not request.path.startswith(reverse('create_profile')) and \
           request.session.get('needs_profile_completion'):
            
            del request.session['needs_profile_completion']
            
            return redirect('create_profile')