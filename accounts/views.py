from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegistrationForm, LoginForm
from .models import DoctorProfile
import random
import re
from django.utils import timezone

def register_view(request):
    registration_success = False
    if request.method == 'POST':
        # Use request.FILES for file upload support
        form = RegistrationForm(request.POST, request.FILES)

        # Validate id_card manually (form field handles it, but double-check)
        if not request.FILES.get('id_card'):
            form.add_error('id_card', 'Doctor ID Card is required.')

        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            mobile = form.cleaned_data['mobile_number']
            id_card_file = request.FILES.get('id_card')

            # Create User with duplicate username handling
            from django.db import IntegrityError
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
            except IntegrityError:
                messages.error(request, "Username already exists. Please choose a different username.")
                return render(request, 'register.html', {'form': form})

            # Generate DOC ID: DOC001, DOC002, ...
            count = DoctorProfile.objects.count() + 1
            doctor_id = f"DOC{count:03d}"
            # Ensure uniqueness
            while DoctorProfile.objects.filter(doctor_id=doctor_id).exists():
                count += 1
                doctor_id = f"DOC{count:03d}"

            # Save profile with status=pending and doctor_id
            try:
                DoctorProfile.objects.create(
                    user=user,
                    mobile_number=mobile,
                    role='doctor',
                    doctor_status='pending',
                    doctor_id=doctor_id,
                    id_card=id_card_file,
                )
            except IntegrityError:
                user.delete()
                messages.error(request, "Mobile number already exists. Please use a different number.")
                return render(request, 'register.html', {'form': form})

            # Obj 3: Stay on same page, show success message at top
            registration_success = True
            form = RegistrationForm()  # reset form
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form, 'registration_success': registration_success})


def custom_login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Feature 3 & 4: Check role and approval status
                try:
                    profile = DoctorProfile.objects.get(user=user)
                    # Admin can always login
                    if profile.role == 'admin':
                        login(request, user)
                        return redirect('admin_dashboard')
                    # Doctors must be approved
                    if profile.doctor_status == 'pending':
                        messages.warning(request, "Wait for admin approval.")
                        return render(request, 'login.html', {'form': form})
                    elif profile.doctor_status == 'rejected':
                        messages.error(request, "Your account has been rejected. Please contact the administrator.")
                        return render(request, 'login.html', {'form': form})
                    # Approved doctor
                    login(request, user)
                    return redirect('dashboard')
                except DoctorProfile.DoesNotExist:
                    # Superuser or users without profile — allow login
                    if user.is_superuser:
                        login(request, user)
                        return redirect('admin_dashboard')
                    login(request, user)
                    return redirect('dashboard')
            else:
                messages.error(request, "Invalid Username or Password")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def forgot_password_view(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile_number')
        try:
            profile = DoctorProfile.objects.get(mobile_number=mobile)
            
            # Generate 4-digit OTP
            otp = str(random.randint(1000, 9999))
            profile.otp = otp
            profile.otp_created_at = timezone.now()
            profile.save()
            
            # --- SIMULATION ONLY (Since no Internet) ---
            print("\n" + "="*40)
            print(f" [SMS GATEWAY] OTP SENT TO {mobile}: {otp}")
            print("="*40 + "\n")
            # -------------------------------------------
            
            request.session['reset_mobile'] = mobile
            messages.info(request, f"OTP sent to {mobile}. (Check your Console Window)")
            return redirect('verify_otp')
            
        except DoctorProfile.DoesNotExist:
            messages.error(request, "Mobile number not registered.")
            
    return render(request, 'forgot_password.html')

def verify_otp_view(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        mobile = request.session.get('reset_mobile')
        new_password = request.POST.get('new_password')
        
        try:
            profile = DoctorProfile.objects.get(mobile_number=mobile)
            if profile.otp == otp_input:
                user = profile.user
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password reset successful! Please login.")
                return redirect('login')
            else:
                messages.error(request, "Invalid OTP.")
        except:
            messages.error(request, "Error resetting password.")
            
    return render(request, 'verify_otp.html')