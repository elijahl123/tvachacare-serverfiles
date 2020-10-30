import calendar
import csv
import datetime
import os
from pathlib import Path

import requests
from django.conf import settings
from django.contrib.auth import logout as lgout, login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.static import serve

from .forms import *
from .models import PatientInformation, Image, SurgeryInformation, Account, ProcedureCodes, EventLog


# Create your views here.
def logout(request):
    event_notes = 'Logged Out'
    event = EventLog(user=request.user.email, event_type='Logged Out', notes=event_notes)
    event.save()
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

    if not request.user.is_accepted:
        return redirect('terms_of_service')

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
            secret_key = settings.RECAPTCHA_SECRET_KEY

            # captcha verification
            data = {
                'response': request.POST.get('recaptcha'),
                'secret': secret_key
            }
            resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result_json = resp.json()

            print(result_json)

            if not result_json.get('success'):
                return render(request, 'loginAdmin.html', {'is_robot': True})
            # end captcha verification
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                event = EventLog(user=email, event_type='Login', notes='Logged In')
                event.save()
                if user.is_accepted:
                    return redirect('home')
                else:
                    return redirect('terms_of_service')
        else:
            email = request.POST['email'] or None
            event = EventLog(user=email, event_type='Failed Login', notes='Failed Login Attempt')
            event.save()

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

    if not request.user.is_accepted:
        return redirect('terms_of_service')

    if request.POST:
        form = AddPatient(request.POST or None, request.FILES or None)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            event_notes = 'Patient ' + str(request.POST['patient_record_number']) + ' was uploaded'
            event = EventLog(user=request.user.email, event_type='Add Patient', notes=event_notes)
            event.save()
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
    surgery = SurgeryInformation.objects.filter(patient=patient.id).order_by('date_of_upload')
    event_notes = 'Patient ID #' + str(patient.id) + ' was Viewed'
    event = EventLog(user=request.user.email, event_type='Patient Viewed', notes=event_notes)
    event.save()
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

    if not request.user.is_accepted:
        return redirect('terms_of_service')

    context['form'] = form
    context['patient'] = patient
    context['surgery'] = surgery
    context['today'] = datetime.date.today()
    return render(request, 'patient_page.html', context)


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
            event_notes = 'Patient ID #' + str(patient.id) + ' was Edited'
            event = EventLog(user=request.user.email, event_type='Patient Edited', notes=event_notes)
            event.save()
            return redirect('patient_page', slug)
    else:
        form = AddPatient

    if not request.user.is_accepted:
        return redirect('terms_of_service')
    context['form'] = form
    context['patient'] = patient
    context['today'] = datetime.date.today()
    return render(request, 'editPatient.html', context)


@login_required
def delete_patient(request, slug):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    patient = get_object_or_404(PatientInformation, slug=slug)
    event_notes = 'Patient ID #' + str(patient.id) + ' was Deleted'
    event = EventLog(user=request.user.email, event_type='Patient Deleted', notes=event_notes)
    event.save()
    patient.delete()
    return redirect('delete_images', slug=slug)


@login_required
def delete_images(request, slug):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    patient = PatientInformation.objects.filter(slug=slug)
    if patient:
        patient.delete()
        return redirect('home')
    else:
        return redirect('home')


@login_required
def approve_surgery(request, slug, id):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.is_approved = True
    surgery.is_denied = False
    surgery.save()
    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Approved'
    event = EventLog(user=request.user.email, event_type='Surgery Approved', notes=event_notes)
    event.save()
    return redirect('home')


@login_required
def deny_surgery(request, slug, id):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.is_denied = True
    surgery.is_approved = False
    surgery.save()
    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Denied'
    event = EventLog(user=request.user.email, event_type='Surgery Denied', notes=event_notes)
    event.save()
    return redirect('home')


@login_required
def add_surgery(request, slug):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
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
            event_notes = 'Surgery Burn Operation Number #' + str(
                request.POST['burn_operation_number']) + ' was uploaded'
            event = EventLog(user=request.user.email, event_type='Add Surgery', notes=event_notes)
            event.save()

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
    if not request.user.is_accepted:
        return redirect('terms_of_service')
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
    surgeries = SurgeryInformation.objects.filter(patient=patient.id).order_by('date_of_upload')
    images = Image.objects.filter(surgery=surgery.id)
    procedure_codes = ProcedureCodes.objects.filter(surgery=surgery.id)

    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Viewed'
    event = EventLog(user=request.user.email, event_type='Surgery Viewed', notes=event_notes)
    event.save()

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
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    surgery = get_object_or_404(SurgeryInformation, id=id)
    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Deleted'
    event = EventLog(user=request.user.email, event_type='Surgery Deleted', notes=event_notes)
    event.save()
    surgery.delete()
    return redirect('delete_surgery_images', slug=slug, id=id)


@login_required
def delete_surgery_images(request, slug, id):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    surgery = SurgeryInformation.objects.filter(id=id)
    if surgery:
        surgery.delete()
        return redirect('patient_page', slug)
    else:
        return redirect('patient_page', slug)


@login_required
def filter_by_date(request):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
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

    if request.user.group == 'Approver':
        return redirect('home')

    submitbutton = request.POST.get('submit')

    context['submitbutton'] = submitbutton

    surgeries = SurgeryInformation._meta.get_fields()
    context['surgeries'] = surgeries

    form = CSVForm(request.POST or None)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        fields = request.POST.get('fields')
        event_notes = 'Filter.csv was created'
        event = EventLog(user=request.user.email, event_type='Filter Created', notes=event_notes)
        event.save()
        if not request.POST.get('procedure_codes'):
            write_response(date_start, date_end, fields)
        else:
            write_response(date_start, date_end, fields, procedure_code_boolean=True)

        return redirect('send_file')

    context['form'] = form
    context['today'] = datetime.date.today()

    return render(request, 'filter.html', context)


def write_response(date_start, date_end, fields, procedure_code_boolean=False):
    with open('filter.csv', 'w', newline="") as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        fields_array = fields.split(',')
        surgeries = SurgeryInformation.objects.filter(date_of_upload__range=[date_start, date_end])
        if surgeries:
            header = [s.replace('patient__', '') for s in fields_array]
            header = [s.replace('_', ' ') for s in header]
            header = [s.title() for s in header]
            if procedure_code_boolean:
                for surgery in surgeries:
                    procedure_codes = ProcedureCodes.objects.filter(surgery=surgery.id)
                    if procedure_codes:
                        for procedure_code in procedure_codes:
                            header.append('Procedure Code')
            wr.writerow(header)
            for surgery in surgeries:
                csv_array = []
                fields_array = [s.replace('patient__', 'patient.') for s in fields_array]
                if fields_array:
                    for field in fields_array:
                        if 'patient.' in field:
                            field = field.replace('patient.', '')
                            attr = getattr(getattr(surgery, 'patient'), field)
                            csv_array.append(attr)
                        elif '' not in fields_array:
                            attr = getattr(surgery, field)
                            csv_array.append(attr)
                        else:
                            break
                if procedure_code_boolean:
                    procedure_codes = ProcedureCodes.objects.filter(surgery=surgery.id)
                    if procedure_codes:
                        for procedure_code in procedure_codes:
                            csv_array.append(procedure_code.procedure_codes)
                wr.writerow(csv_array)

        else:
            wr.writerows('')
        wr.writerow('')
    with open('filter.csv', 'r') as myfile:
        response = HttpResponse(myfile, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=filter.csv'
        return response


@login_required
def send_file(request):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'filter.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
def calendar_events(request, year, current_month):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
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


def hui_report(request):
    if not request.user.is_accepted:
        return redirect('terms_of_service')
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
        fields = 'patient__first_name,patient__last_name,date_of_surgery,patient__patient_record_number,is_approved'
        event_notes = 'HUI Report was created'
        event = EventLog(user=request.user.email, event_type='Report Created', notes=event_notes)
        event.save()
        write_response(date_start, date_end, fields, procedure_code_boolean=True)

        return redirect('send_file')

    context['form'] = form
    context['today'] = datetime.date.today()

    return render(request, 'hui_filter.html', context)


def privacyPolicy(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context = {"account": account, 'today': datetime.date.today()}
    return render(request, 'privacyPolicy.html', context)


def terms_of_service(request):
    context = {}

    if request.POST:
        if 'accept' in request.POST:
            account = get_object_or_404(Account, id=request.user.id)
            account.is_accepted = True
            account.save()
            return redirect('home')
        else:
            return redirect('logout')

    return render(request, 'terms_of_service.html', context)
