from django.shortcuts import render

def top(request):
    return render(request, 'index.html')

def terms_of_service(request):
    return render(request, 'terms-of-service.html')
