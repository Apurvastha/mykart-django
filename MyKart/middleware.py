# from django.contrib.auth.middleware import SessionAuthenticationMiddleware
# from django.contrib.auth.views import login
# from django.urls import reverse


# class AdminSessionMiddleware(SessionAuthenticationMiddleware):
#     def process_request(self, request):
#         if request.path.startswith(reverse('admin:index')):
#             request.session.set_test_cookie()
#         return super().process_request(request)

#     def process_response(self, request, response):
#         if request.path.startswith(reverse('admin:index')):
#             response = super().process_response(request, response)
#             if request.session.test_cookie_worked():
#                 request.session.delete_test_cookie()
#         return response