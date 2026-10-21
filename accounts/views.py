from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegisterForm

#RF-24: Register Account
def register_account(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()   
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

#RF-29: Log in with account credentials

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Only follow ?next= to pages on this site, never to another domain.
            next_url = request.POST.get('next', '')
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('/')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': request.GET.get('next', request.POST.get('next', ''))})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('/')


#RF-36: Change account password

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Saving a new password rotates the session hash, which would log
            # this user out on the next request. This re-signs their session
            # so only other devices are logged out.
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña se cambió correctamente.')
            return redirect('index')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})