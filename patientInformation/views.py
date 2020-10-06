import calendar
import csv
import datetime
import os
from pathlib import Path

import requests
from django.contrib.auth import logout as lgout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from django.forms import modelformset_factory, formset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.static import serve

from .forms import AccountAuthenticationForm, AccountUpdateForm, AddPatient, ImageForm, SurgeryForm, CSVForm, EmailForm, \
    ProcedureForm
from .models import PatientInformation, Image, SurgeryInformation, Account, ProcedureCodes


# Create your views here.
def logout(request):
    lgout(request)
    return redirect("login")


def index(request):
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

    context = {'account': account, 'today': datetime.date.today()}
    if request.user.is_authenticated:
        if request.user.group == 'Approver':
            surgery = SurgeryInformation.objects.all()
            context['object'] = surgery
        else:
            patient = PatientInformation.objects.all()
            surgery = SurgeryInformation.objects.all()
            context['object'] = patient
            context['surgery'] = surgery

    if not request.user.is_authenticated:
        return redirect('login')

    if request.POST:
        form = AccountUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
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
        context['today'] = datetime.date.today()
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
    context['today'] = datetime.date.today()
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
    context['today'] = datetime.date.today()

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
            response = requests.get(patient.patient_image.url)
            email.attach(patient.patient_image.name, response.content, mimetype='image/*')
        if patient.injury_image:
            response = requests.get(patient.injury_image.url)
            email.attach(patient.injury_image.name, response.content, mimetype='image/*')
        email.send()

    context['form'] = form
    context['patient'] = patient
    context['surgery'] = surgery
    context['today'] = datetime.date.today()
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
def approve_surgery(request, slug, id):
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.is_approved = True
    surgery.is_denied = False
    surgery.save()
    return redirect('home')


@login_required
def deny_surgery(request, slug, id):
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.is_denied = True
    surgery.is_approved = False
    surgery.save()
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
    ImageFormSet = formset_factory(ImageForm, extra=0)
    ProcedureFormSet = formset_factory(ProcedureForm, extra=0)

    if request.method == 'POST':
        surgeryForm = SurgeryForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, prefix='images')
        formset_procedure_codes = ProcedureFormSet(request.POST, request.FILES, prefix='procedures')
        if surgeryForm.is_valid() or formset.is_valid() or formset_procedure_codes.is_valid():
            surgery_form = surgeryForm.save(commit=False)
            surgery_form.save()

            for form in formset.cleaned_data:
                image = form['image']
                date_of_upload_image = form['date_of_upload_image']
                photo = Image(surgery=surgery_form, image=image, date_of_upload_image=date_of_upload_image)
                photo.save()
            for form in formset_procedure_codes.cleaned_data:
                procedure_codes = form['procedure_codes']
                procedure = ProcedureCodes(surgery=surgery_form, procedure_codes=procedure_codes)
                procedure.save()
            return redirect('patient_page', slug)
    else:
        surgeryForm = SurgeryForm()
        formset = ImageFormSet(prefix='images')
        formset_procedure_codes = ProcedureFormSet(prefix='procedures')
    return render(request, 'addSurgery.html',
                  {'surgeryForm': surgeryForm, 'formset': formset, 'formset_procedure_codes': formset_procedure_codes,
                   'account': account, 'patient': patient, 'today': datetime.date.today()})


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
    procedure_codes = ProcedureCodes.objects.filter(surgery=surgery.id)

    context['patient'] = patient
    context['surgery'] = surgery
    context['images'] = images
    context['surgeries'] = surgeries
    context['procedure_codes'] = procedure_codes
    context['today'] = datetime.date.today()
    if request.POST:
        if 'approve' in request.POST:
            surgery.reason = request.POST['reason']
            surgery.save()
            approve_surgery(request, surgery.patient.slug, surgery.id)
            return redirect('home')
        elif 'deny' in request.POST:
            surgery.reason = request.POST['reason']
            surgery.save()
            deny_surgery(request, surgery.patient.slug, surgery.id)
            return redirect('home')
        elif 'appeal' in request.POST:
            subject = 'Appeal Request for ' + patient.first_name + ' ' + patient.last_name + ' Surgery ID #' + str(
                surgery.id)
            to_emails = Account.objects.filter(group='Approver').values_list('email', flat=True)
            message = request.POST.get('appeal_request')
            html_message = render_to_string('appeal_email.html',
                                            {'patient': patient, 'account': account, 'message': message,
                                             'surgery': surgery})
            for email in to_emails:
                send_mail(subject, message, from_email='tvachacare@gmail.com', recipient_list=[email],
                          html_message=html_message)
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
        return redirect('patient_page', slug)
    else:
        return redirect('patient_page', slug)


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
    context['today'] = datetime.date.today()

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
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'filter.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
def edit_patient(request, slug):
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
    if request.POST:
        form = AddPatient(request.POST or None, request.FILES or None, instance=patient)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            form = AddPatient()
            return redirect('patient_page', slug)
    else:
        form = AddPatient

    context['form'] = form
    context['patient'] = patient
    context['today'] = datetime.date.today()
    return render(request, 'editPatient.html', context)


@login_required
def calendar_events(request, year, current_month):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    this_month = calendar.month_name[int(current_month)]
    c = calendar.Calendar(6)
    this_calendar = c.monthdatescalendar(int(year), int(current_month))
    context = {"account": account,
               'calendar': this_calendar,
               'month': this_month,
               'year': year,
               'month_num': int(current_month)}
    patient = PatientInformation.objects.all()
    surgeries = SurgeryInformation.objects.all()
    context['patient'] = patient
    context['surgeries'] = surgeries
    context['today'] = datetime.date.today()
    return render(request, 'calendar.html', context)
