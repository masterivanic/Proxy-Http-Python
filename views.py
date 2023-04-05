from django.shortcuts import render

# Create your views here.


def index(request):
    print("------------ request answer --------", request, end="")
    return render(request, 'index.html', {})
