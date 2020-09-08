import csv
import os

from django.conf import settings
from django.contrib.auth import logout as lgout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.static import serve

from .forms import AccountAuthenticationForm, AccountUpdateForm, AddPatient, ImageForm, SurgeryForm, CSVForm, EmailForm
from .models import PatientInformation, Image, SurgeryInformation


# Create your views here.
def logout(request):
    lgout(request)
    return redirect("login")


def index(request):
    if request.user.is_authenticated:
        if request.user.group == 'Approver':
            patient = PatientInformation.objects.filter(is_approved=False)
        else:
            patient = PatientInformation.objects.all()
    if not request.user.is_authenticated:
        return redirect('login')
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "profile_picture_path": request.user.profile_picture_path,
        'group': request.user.group,
        'is_superuser': request.user.is_superuser
    } if request.user.is_authenticated else None

    context = {
        'object': patient,
        'account': account
    }

    if request.POST:
        form = AccountUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        else:
            form = AccountUpdateForm(
                initial={
                    'email': request.user.email,
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'profile_picture_path': request.user.profile_picture_path,
                }
            )
        context['account_form'] = form
    return render(request, 'homePage.html', context)


def loginPage(request):
    return render(request, 'login.html', {})


def loginadmin(request):
    context = {}

    user = request.user

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                return redirect('home')

    else:
        form = AccountAuthenticationForm()

    context['login_form'] = form
    return render(request, 'loginAdmin.html', context)


@login_required
def addpatient(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "profile_picture_path": request.user.profile_picture_path,
        "is_superuser": request.user.is_superuser,
        'group': request.user.group,
    } if request.user.is_authenticated else None

    context = {
        "account": account
    }

    if request.POST:
        form = AddPatient(request.POST or None, request.FILES or None)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            form = AddPatient()
            return redirect('home')
    else:
        form = AddPatient

    context['form'] = form

    if request.user.group == 'Data Entry':
        return render(request, 'addPatient.html', context)
    elif request.user.is_superuser:
        return render(request, 'addPatient.html', context)
    else:
        return redirect('home')


@login_required
def patient_page(request, slug):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context = {
        "account": account,
    }
    patient = get_object_or_404(PatientInformation, slug=slug)
    surgery = SurgeryInformation.objects.filter(patient=patient.id)
    form = EmailForm(request.POST or None)
    if form.is_valid():
        to = request.POST.get('to')
        cc = request.POST.get('cc')
        bcc = request.POST.get('bcc')
        from_email = request.POST.get('from_email')
        title = str('<From: ' + from_email + '>' + request.POST.get('title'))
        if patient.story:
            story = patient.story
        else:
            story = ''
        message = request.POST.get('message')
        plain_text = str(story + message)
        to = to.split(',')
        cc = cc.split(',')
        bcc = bcc.split(',')
        html_message = str('<main style="width: 90%;background-color: white;padding: 50px;"><h1 style="color: ' +
                           '#fc9c34;font-family: Raleway, sans-serif;font-weight: bold;">' + patient.first_name + ' ' +
                           patient.last_name + '</h1><p style="color: #fc9c34;">' + story +
                           '</p><p style="color: #fc9c34;">' + message + '</p></main>')
        email = EmailMessage(
            subject=title,
            body=html_message,
            to=to,
            cc=cc,
            bcc=bcc,
            from_email=from_email,
            headers={'From': from_email}
        )
        email.content_subtype = 'html'
        if patient.patient_image:
            response = request.get(patient.patient_image.url)
            email.attach('Patient Image', response.read())
        if patient.injury_image:
            response = request.get(patient.injury_image.url)
            email.attach('Injury Image', response.read())
        email.send()

    context['form'] = form
    context['patient'] = patient
    context['surgery'] = surgery
    return render(request, 'patient_page.html', context)


@login_required
def delete_patient(request, slug):
    patient = get_object_or_404(PatientInformation, slug=slug)
    patient.delete()
    return redirect('delete_images', slug=slug)


@login_required
def delete_images(request, slug):
    patient = PatientInformation.objects.filter(slug=slug)
    if patient:
        patient.delete()
        return redirect('home')
    else:
        return redirect('home')


@login_required
def approve_patient(request, slug):
    patient = get_object_or_404(PatientInformation, slug=slug)
    patient.is_approved = True
    patient.save()
    return redirect('home')


@login_required
def add_surgery(request, slug):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "is_superuser": request.user.is_superuser,
        'group': request.user.group,
    } if request.user.is_authenticated else None

    patient = get_object_or_404(PatientInformation, slug=slug)
    ImageFormSet = modelformset_factory(Image, form=ImageForm, extra=0)

    if request.method == 'POST':
        surgeryForm = SurgeryForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        patient.is_approved = False
        patient.save()
        if surgeryForm.is_valid() or formset.is_valid():
            surgery_form = surgeryForm.save(commit=False)
            surgery_form.save()

            for form in formset.cleaned_data:
                image = form['image']
                photo = Image(surgery=surgery_form, image=image)
                photo.save()
            return redirect('patient_page', slug)
    else:
        surgeryForm = SurgeryForm()
        formset = ImageFormSet(queryset=Image.objects.none())
    return render(request, 'addSurgery.html',
                  {'surgeryForm': surgeryForm, 'formset': formset, 'account': account, 'patient': patient})


@login_required
def surgery_page(request, slug, id):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context = {
        "account": account,
    }
    patient = get_object_or_404(PatientInformation, slug=slug)
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgeries = SurgeryInformation.objects.filter(patient=patient.id)
    images = Image.objects.filter(surgery=surgery.id)
    context['patient'] = patient
    context['surgery'] = surgery
    context['images'] = images
    context['surgeries'] = surgeries
    return render(request, 'surgery_page.html', context)


@login_required
def delete_surgery(request, slug, id):
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.delete()
    return redirect('delete_surgery_images', slug=slug, id=id)


@login_required
def delete_surgery_images(request, slug, id):
    surgery = SurgeryInformation.objects.filter(id=id)
    if surgery:
        surgery.delete()
        return redirect('home')
    else:
        return redirect('home')


@login_required
def filter_by_date(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context = {
        "account": account,
    }

    submitbutton = request.POST.get('submit')

    context['submitbutton'] = submitbutton

    surgeries = SurgeryInformation._meta.get_fields()
    context['surgeries'] = surgeries

    form = CSVForm(request.POST or None)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        fields = request.POST.get('fields')
        write_response(date_start, date_end, fields)
        return redirect('send_file')

    context['form'] = form

    return render(request, 'filter.html', context)


def write_response(date_start, date_end, fields):
    with open('filter.csv', 'w', newline="") as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        fields_array = fields.split(',')
        surgeries = SurgeryInformation.objects.filter(date_of_upload__range=[date_start, date_end]).values_list(
            *fields_array)
        if surgeries:
            header = [s.replace('patient__', '') for s in fields_array]
            header = [s.replace('_', ' ') for s in header]
            header = [s.title() for s in header]
            wr.writerow(header)
            for surgery in surgeries:
                wr.writerow(surgery)

        else:
            wr.writerows('')
        wr.writerow('')
    with open('filter.csv', 'r') as myfile:
        response = HttpResponse(myfile, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=filter.csv'
        return response


@login_required
def send_file(request):
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'filter.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))
