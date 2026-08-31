from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegisterForm

#RF-24: Register Account
def register_account(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()   
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})