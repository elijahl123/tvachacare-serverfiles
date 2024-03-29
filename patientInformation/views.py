#  Copyright (c) 2020 Elijah Lopez
#
#  TvachaCare grants to you a personal, non-exclusive, non-assignable and
#  non-transferable license to use and display the software provided by
#  or on behalf of TvachaCare (including any updates) only for the purpose
#  of accessing the Service ("Software") on any computer(s) on which you
#  are the primary user or which you are authorized to use. Our Privacy
#  Policies provide important information about the Software applications
#  we utilize. Please read the terms very carefully, as they contain important
#  disclosures about the use and security of data transmitted to and from
#  your computer. Unauthorized copying of the Software, including, without
#  limitation, software that has been modified, merged or included with
#  the Software, or the written materials associated therewith, is expressly
#  forbidden. You may not sublicense, assign, or transfer this license or
#  the Software except as permitted in writing by TvachaCare. Any attempt
#  to sublicense, assign or transfer any of the rights, duties or obligations
#  under this license is void and may result in termination by TvachaCare
#  of this license. You agree that you shall not copy or duplicate or permit
#  anyone else to copy or duplicate any part of the Software, or create
#  or attempt to create, or permit others to create or attempt to create,
#  by reverse engineering or otherwise, the source programs or any part
#  thereof from the object programs or from other information made available
#  under this Agreement.
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

import calendar
import csv
import datetime
import operator
import os
from functools import reduce
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as lgout, login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import FieldError
from django.core.mail import EmailMessage
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.static import serve

from TvachaCare.settings import BASE_DIR
from account.forms import *
from account.models import Account
from patientInformation.forms import *
from .models import PatientInformation, Image, SurgeryInformation, ProcedureCodes, EventLog, Appeal

"""
This is a guide to the different context objects I use for each view: 

context['account'] is the request's user. If the user is authenticated, it will show the Account model *required 

context['title'] is only for when there is a form that uses the General Form Template *required 

context['different_fields'] is for when there is a form template. It is a list of the field names that will not show 
up on general for loop. Use only when you have different types of inputs or you just don't want the user to see it. 

context['

"""

context = {'today': datetime.date.today()}  # Theses are all the non view-specific context variables


def terms_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='/terms-of-service/'):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_accepted,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def try_sort_by(sort_by: str, context: dict, obj, excluded_fields=None, *args, **kwargs):
    if excluded_fields is None:
        excluded_fields = []
    try:
        queryset = obj.objects.filter(*args, **kwargs).order_by(
            sort_by) if args or kwargs else obj.objects.all().order_by(sort_by)
        context['sort_by'] = {
            'field': sort_by.replace('_', ' ').replace('-', ''),
            'value': sort_by.replace('-', ''),
            'first_val': '' if sort_by[0] == '-' else '-'
        }
        context['field_error'] = ''
    except FieldError:
        queryset = obj.objects.filter(*args, **kwargs) if args or kwargs else obj.objects.all()
        context['sort_by'] = ''
        context['field_error'] = \
            f"'{sort_by.replace('_', ' ').replace('-', '').capitalize()}' does not exist" \
                if sort_by else ''
    finally:
        context['object_name'] = obj._meta.verbose_name if queryset.count() == 1 else obj._meta.verbose_name_plural
        context['field_list'] = [field for field in obj._meta.get_fields()]
        context['excluded_fields'] = excluded_fields
    return queryset


@login_required
@terms_required
def add_surgery(request, slug):
    if not request.user.group.can_add_surgeries:
        return redirect('home')

    context['account'] = request.user
    context['title'] = 'Add Surgery'
    context['different_fields'] = ['patient', 'area_operated']

    patient = get_object_or_404(PatientInformation, slug=slug)
    image_form_set = formset_factory(ImageForm, extra=0)

    if request.POST:
        surgery_form = SurgeryForm(request.POST, error_class=DivErrorList)
        formset = image_form_set(request.POST, request.FILES, prefix='images')
        if surgery_form.is_valid() and formset.is_valid():
            obj = surgery_form.save(commit=False)
            obj.save()
            surgery_form = SurgeryForm
            messages.add_message(request, messages.SUCCESS,
                                 'Surgery #%s was created successfully!' % obj.id)

            procedures = request.POST.getlist('procedures[]')

            for procedure in procedures:
                obj = ProcedureCodes(procedure_codes=procedure, surgery=obj)
                obj.save()

            for form in formset.cleaned_data:
                image = form['image']
                date_of_upload_image = form['date_of_upload_image']
                photo = Image(surgery=obj, image=image, date_of_upload_image=date_of_upload_image)
                photo.save()
            return redirect('patient_page', slug)
    else:
        surgery_form = SurgeryForm
        formset = image_form_set(prefix='images')
    context['form'] = surgery_form
    context['formset'] = formset
    context['patient'] = patient
    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def addpatient(request):
    account = request.user if request.user.is_authenticated else None

    context['account'] = account

    if not request.user.group.can_add_patients:
        return redirect('home')

    context['title'] = 'Add Patient'
    context['different_fields'] = PatientInformation.different_fields

    if request.POST:
        form = AddPatient(request.POST or None, request.FILES or None, error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            form = AddPatient()
            messages.add_message(request, messages.SUCCESS,
                                 'Patient %s was created successfully!' % obj.patient_record_number)
            return redirect('home')
    else:
        form = AddPatient()

    context['form'] = form

    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def approve_surgery(request, slug, surgery_id):
    surgery = get_object_or_404(SurgeryInformation, id=surgery_id)
    surgery.is_approved = True
    surgery.is_denied = False
    surgery.approver = request.user
    surgery.save()
    event_notes = f'Surgery ID #{str(surgery_id)} was Approved. Reason: {surgery.reason}'
    event = EventLog(event_type='Surgery Approved', notes=event_notes, color='success', icon='fas fa-check')
    event.save()
    return redirect('home')


@login_required
@terms_required
def calendar_events(request, year, current_month):
    account = request.user if request.user.is_authenticated else None
    this_month = calendar.month_name[int(current_month)]
    c = calendar.Calendar(6)
    this_calendar = c.monthdatescalendar(int(year), int(current_month))
    context['account'] = account
    context['calendar'] = this_calendar
    context['month'] = this_month
    context['year'] = year
    context['month_num'] = int(current_month)
    patient = PatientInformation.objects.all()
    surgeries = SurgeryInformation.objects.all()
    context['patient'] = patient
    context['surgeries'] = surgeries
    return render(request, 'calendar.html', context)


@login_required
@terms_required
def delete_images(request, slug):
    patient = PatientInformation.objects.filter(slug=slug)
    if patient:
        patient.delete()
        return redirect('home')
    return redirect('home')


@login_required
@terms_required
def delete_patient(request, slug):
    patient = get_object_or_404(PatientInformation, slug=slug)
    if request.POST:
        messages.add_message(request, messages.SUCCESS,
                             'Patient %s was deleted successfully!' % patient.patient_record_number)
        patient.delete()
        return redirect('delete_images', slug=slug)
    context['title'] = 'Delete Patient'
    context['objects'] = [patient]
    return render(request, 'delete_object.html', context)


@login_required
@terms_required
def delete_surgery(request, slug, surgery_id):
    surgery = get_object_or_404(SurgeryInformation, id=surgery_id)
    messages.add_message(request, messages.SUCCESS,
                         'Surgery #%s was deleted successfully!' % surgery.id)
    surgery.delete()

    return redirect('delete_surgery_images', slug=slug, surgery_id=surgery_id)


@login_required
@terms_required
def delete_surgery_images(request, slug, surgery_id):
    surgery = SurgeryInformation.objects.filter(id=surgery_id)
    if surgery:
        surgery.delete()
        return redirect('patient_page', slug)
    return redirect('patient_page', slug)


@login_required
@terms_required
def deny_surgery(request, slug, surgery_id):
    surgery = get_object_or_404(SurgeryInformation, id=surgery_id)
    surgery.is_denied = True
    surgery.is_approved = False
    surgery.approver = request.user
    surgery.save()
    event_notes = f'Surgery ID #{str(surgery_id)} was Denied. Reason: {surgery.reason}'
    event = EventLog(event_type='Surgery Denied', notes=event_notes, color='danger', icon='fas fa-times')
    event.save()
    return redirect('home')


@login_required
@terms_required
def edit_patient(request, slug):
    account = request.user if request.user.is_authenticated else None
    context['account'] = account
    patient = get_object_or_404(PatientInformation, slug=slug)
    if request.POST:
        form = AddPatient(request.POST or None, request.FILES or None, instance=patient)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return redirect('patient_page', slug)
    else:
        form = AddPatient(instance=patient)

    context['form'] = form
    context['patient'] = patient
    context['different_fields'] = PatientInformation.different_fields
    context['title'] = 'Edit Patient'
    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def filter_by_date(request):
    account = request.user if request.user.is_authenticated else None
    context['account'] = account

    if request.user.group.name == 'Approver':
        return redirect('home')

    submitbutton = request.POST.get('submit')

    context['submitbutton'] = submitbutton

    surgeries = SurgeryInformation._meta.get_fields()
    context['surgeries'] = surgeries
    patients = PatientInformation._meta.get_fields()
    context['patients'] = patients

    form = CSVForm(request.POST or None)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        fields = request.POST.getlist('checks[]')
        messages.add_message(request, messages.SUCCESS,
                             'Filter was created successfully!')
        if not request.POST.get('procedure_codes'):
            write_response(date_start, date_end, fields)
        else:
            write_response(date_start, date_end, fields, procedure_code_boolean=True)

        return redirect('send_file')

    context['form'] = form

    return render(request, 'filter/filter.html', context)


@login_required
@terms_required
def hui_report(request):
    account = request.user if request.user.is_authenticated else None
    context['account'] = account

    submitbutton = request.POST.get('submit')

    context['submitbutton'] = submitbutton

    surgeries = SurgeryInformation._meta.get_fields()
    context['surgeries'] = surgeries

    form = CSVForm(request.POST or None)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        fields = ['patient__first_name', 'patient__last_name', 'date_of_surgery', 'patient__patient_record_number',
                  'is_approved']
        event_notes = 'HUI Report was created'
        event = EventLog(event_type='Report Created', notes=event_notes)
        event.save()
        write_response(date_start, date_end, fields, procedure_code_boolean=True)

        return redirect('send_file')

    context['form'] = form

    return render(request, 'filter/hui_filter.html', context)


@login_required
@terms_required
def index(request):
    context['account'] = request.user if request.user.is_authenticated else None
    if 'sort-by' in request.GET:
        request.session['sort_by'] = request.GET.get('sort-by')
    sort_by = request.session.get('sort_by', '')

    if request.user.group.can_approve:
        surgery = try_sort_by(sort_by, context, SurgeryInformation, excluded_fields=['image', 'procedurecodes'],
                              is_approved=False, is_denied=False)
        context['object'] = surgery
        context['object_name'] = 'Surgery Awaiting Approval' if surgery.count() == 1 else 'Surgeries Awaiting Approval'
        template = 'approver_index.html'
    else:
        patient = try_sort_by(sort_by, context, PatientInformation,
                              ['patient_image', 'injury_image', 'surgeryinformation'])
        context['object'] = patient
        template = 'index.html'

    return render(request, template, context)


@login_required
@terms_required
def approved_and_denied(request):
    context['account'] = request.user
    context['approved'] = SurgeryInformation.objects.filter(is_approved=True)
    context['denied'] = SurgeryInformation.objects.filter(is_denied=True)
    return render(request, 'approved_and_denied.html', context)


def loginadmin(request):
    user = request.user

    if request.user.is_authenticated:
        return redirect('home')

    context['account'] = request.user if user.is_authenticated else None

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
            result_json = resp.json().get('score')

            if result_json >= 0.7:
                user = authenticate(email=email, password=password)
            else:
                return redirect('logout')

            if user:
                login(request, user)
                if user.is_accepted:
                    if request.GET.get('next'):
                        return HttpResponseRedirect(request.GET.get('next'))
                    return redirect('home')
                else:
                    return redirect('terms_of_service')
        else:
            email = request.POST['email'] or None

    else:
        form = AccountAuthenticationForm()

    context['login_form'] = form
    return render(request, 'account/loginAdmin.html', context)


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'account/login.html', {'groups': Group.objects.all()})


def logout(request):
    if not request.user.is_authenticated:
        return redirect('login')
    lgout(request)
    return redirect("login")


@login_required
@terms_required
def patient_page(request, slug):
    context['account'] = request.user if request.user.is_authenticated else None
    patient = get_object_or_404(PatientInformation, slug=slug)
    surgery = SurgeryInformation.objects.filter(patient=patient.id).order_by('date_of_upload')
    if request.POST:
        form = EmailForm(request.POST or None)
        if form.is_valid():
            to = request.POST.get('to')
            cc = request.POST.get('cc')
            bcc = request.POST.get('bcc')
            from_email = request.POST.get('name') + ' <contact@tvachacare.com>'
            title = str(request.POST.get('title'))
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
            )
            email.content_subtype = 'html'
            if patient.patient_image:
                response = requests.get(request.build_absolute_uri(patient.patient_image.url))
                email.attach(patient.patient_image.name, response.content, mimetype='image/*')
            if patient.injury_image:
                response = requests.get(request.build_absolute_uri(patient.injury_image.url))
                email.attach(patient.injury_image.name, response.content, mimetype='image/*')
            email.send()
    else:
        form = EmailForm()
    context['form'] = form
    context['patient'] = patient
    highlighted_fields = ['first_name',
                          'middle_name',
                          'last_name',
                          'patient_image',
                          'injury_image',
                          'uploaded',
                          'age',
                          'gender',
                          'patient_record_number',
                          'surgeryinformation',
                          'slug'
                          ]
    fields = [field for field in PatientInformation._meta.get_fields() if field.name not in highlighted_fields]
    fields_tuple = []

    for field in fields:
        fields_tuple.append((field.name.replace('_', ' ').capitalize(), getattr(patient, field.name)))

    context['fields'] = fields_tuple

    surgery_tuple = []

    for surgeries in surgery:
        try:
            surgery_tuple.append((surgeries, Image.objects.filter(surgery=surgeries)[0]))
        except IndexError:
            surgery_tuple.append((surgeries, None))
    context['surgery'] = surgery_tuple
    return render(request, 'patients/patient_page.html', context)


@login_required
@terms_required
def send_file(request):
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'filter.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
@terms_required
def surgery_page(request, slug, surgery_id):
    context['account'] = request.user if request.user.is_authenticated else None
    patient = get_object_or_404(PatientInformation, slug=slug)
    surgery = get_object_or_404(SurgeryInformation, id=surgery_id)
    surgeries = SurgeryInformation.objects.filter(patient=patient.id).order_by('date_of_upload')
    images = Image.objects.filter(surgery=surgery.id)
    procedure_codes = ProcedureCodes.objects.filter(surgery=surgery.id)

    highlighted_fields = [
        'image',
        'procedurecodes',
        'patientinformation',
        'patient',
        'date_of_surgery',
        'date_of_admission',
        'date_of_discharge',
        'approver',
        'reason',
        'appeal'
    ]
    fields = [field for field in SurgeryInformation._meta.get_fields() if field.name not in highlighted_fields]
    fields_tuple = []

    for field in fields:
        fields_tuple.append((field.name.replace('_', ' ').capitalize(), getattr(surgery, field.name)))

    context['fields'] = fields_tuple

    surgery_tuple = []

    for surgeries in surgeries:
        try:
            surgery_tuple.append((surgeries, Image.objects.filter(surgery=surgeries)[0]))
        except IndexError:
            surgery_tuple.append((surgeries, None))
    context['surgeries'] = surgery_tuple

    context['images'] = images
    context['surgery'] = surgery
    context['patient'] = patient
    if request.POST:
        if 'approve' in request.POST:
            surgery.reason = request.POST['reason']
            surgery.save()
            approve_surgery(request, surgery.patient.slug, surgery.id)
            messages.add_message(request, messages.SUCCESS,
                                 'Surgery #%s was approved' % surgery.id)
            return redirect('home')
        if 'deny' in request.POST:
            surgery.reason = request.POST['reason']
            surgery.save()
            deny_surgery(request, surgery.patient.slug, surgery.id)
            messages.add_message(request, messages.SUCCESS,
                                 'Surgery #%s was denied' % surgery.id)
            return redirect('home')
        if 'appeal' in request.POST:
            appeal = Appeal.objects.create(surgery=surgery, message=request.POST.get('appeal_request', ''))
            messages.success(request, f'Appeal Successfully Created')
            return redirect('surgery_page', patient.slug, surgery.id)

    return render(request, 'surgeries/surgery_page.html', context)


def terms_of_service(request):
    context['account'] = request.user if request.user.is_authenticated else None
    if request.POST:
        if 'accept' in request.POST:
            account = get_object_or_404(Account, id=request.user.id)
            account.is_accepted = True
            account.save()
            if 'next' in request.GET:
                return HttpResponseRedirect(request.GET.get('next'))
            return redirect('home')
        else:
            return redirect('logout')

    return render(request, 'terms_of_service.html', context)


@login_required
@terms_required
def add_image(request, slug, surgery_id):
    context['account'] = request.user
    context['title'] = 'Add Image'
    context['different_fields'] = Image.different_fields
    if request.POST:
        form = AddImage(request.POST or None, request.FILES or None, error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return redirect('edit_surgery', slug, surgery_id)
    else:
        form = AddImage()
    context['form'] = form
    context['surgery'] = get_object_or_404(SurgeryInformation, id=surgery_id)
    return render(request, 'generic_form_template.html', context)


def write_response(date_start, date_end, fields, procedure_code_boolean=False):
    with open('filter.csv', 'w', newline="") as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        fields_array = fields
        surgeries = SurgeryInformation.objects.filter(date_of_upload__range=[date_start, date_end])
        if surgeries:
            header = [s.replace('patient__', '') for s in fields_array]
            header = [s.replace('_', ' ') for s in header]
            header = [s.title() for s in header]
            if procedure_code_boolean:
                header.append('Procedure Codes:')
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
@terms_required
def edit_surgery(request, slug, surgery_id):
    context['account'] = request.user
    context['title'] = 'Edit Surgery'
    context['different_fields'] = []
    if request.POST:
        form = SurgeryForm(request.POST or None, instance=get_object_or_404(SurgeryInformation, id=surgery_id),
                           error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return redirect('surgery_page', slug, surgery_id)
    else:
        form = SurgeryForm(instance=get_object_or_404(SurgeryInformation, id=surgery_id))
    context['form'] = form
    surgery = get_object_or_404(SurgeryInformation, id=surgery_id)
    context['surgery'] = surgery
    context['images'] = Image.objects.filter(surgery=surgery)
    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def edit_image(request, slug, surgery_id, image_id):
    context['account'] = request.user
    context['title'] = 'Edit Image'
    context['different_fields'] = Image.different_fields
    if request.POST:
        form = ImageForm(request.POST or None, request.FILES or None, instance=get_object_or_404(Image, id=image_id),
                         error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return redirect('edit_surgery', slug, surgery_id)
    else:
        form = ImageForm(instance=get_object_or_404(Image, id=image_id))
    context['form'] = form
    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def delete_image(request, image_id):
    context['account'] = request.user
    image = get_object_or_404(Image, id=image_id)
    image.delete()
    return redirect('edit_surgery', image.surgery.patient.slug, image.surgery.id)


@login_required
@terms_required
def report_bug(request):
    context['account'] = request.user
    context['title'] = 'Report Bug'
    if request.POST:
        form = ReportForm(request.POST or None, error_class=DivErrorList)
        if form.is_valid():
            subject = request.POST['title']
            message = request.POST['description']
            from_email = request.user.first_name + ' ' + request.user.last_name + ' ' + 'via TvachaCare ' \
                                                                                        '<contact@tvachacare.com> '
            email = EmailMessage(subject=subject, body=message, from_email=from_email,
                                 to=['elijah.kane.1972@gmail.com'])
            email.send()
            return redirect('home')
    else:
        form = ReportForm()
    context['form'] = form
    context['different_fields'] = []
    return render(request, 'generic_form_template.html', context)


def error_404(request, exception):
    context['account'] = request.user
    context['exception'] = {
        'number': '404',
        'value': 'Page Not Found'
    }
    return render(request, 'errors/404_page.html', context)


def error_500(request):
    context['account'] = request.user
    context['exception'] = {
        'number': '500',
        'value': 'Internal Server Error'
    }

    return render(request, 'errors/404_page.html', context)


@login_required
@terms_required
def waiting_list(request):
    context['account'] = request.user
    if not request.user.group.name == 'Admin':
        return redirect('home')
    context['form'] = WaitingRoomForm()
    patients = PatientInformation.objects.filter(in_waiting_room=True)
    other_patients = PatientInformation.objects.filter(in_waiting_room=False)
    context['patients'] = patients
    context['other_patients'] = other_patients
    if request.POST and 'remove_all' in request.POST:
        patients.update(in_waiting_room=False)
    return render(request, 'waiting list/waiting_list.html', context)


@login_required
@terms_required
def waiting_list_search(request):
    context['account'] = request.user
    if not request.user.group.name == 'Admin':
        return redirect('home')
    context['form'] = WaitingRoomForm()
    query = []
    for item in request.GET:
        value = request.GET.get(item)
        if value:
            arguments = {f'{item}__iexact': value}
            q_object = Q(**arguments)
            query.append(q_object)
    if query:
        patients = PatientInformation.objects.filter(reduce(operator.and_, query))
    else:
        patients = PatientInformation.objects.all()

    context['patients'] = patients

    if request.POST and 'add_all' in request.POST:
        patients.update(in_waiting_room=True)
        return redirect('waiting_list')

    return render(request, 'waiting list/waiting_list_search.html', context)


@login_required
@terms_required
def waiting_list_add(request, patient_id):
    context['account'] = request.user
    if not request.user.group.name == 'Admin':
        return redirect('home')
    patient = get_object_or_404(PatientInformation, id=patient_id)
    patient.in_waiting_room = True
    patient.save()
    return redirect('waiting_list')


@login_required
@terms_required
def waiting_list_remove(request, patient_id):
    context['account'] = request.user
    if not request.user.group.name == 'Admin':
        return redirect('home')
    patient = get_object_or_404(PatientInformation, id=patient_id)
    patient.in_waiting_room = False
    patient.save()
    return redirect('waiting_list')


@login_required
@terms_required
def export_waiting_list(request):
    context['account'] = request.user
    if not request.user.group.name == 'Admin':
        return redirect('home')
    patients = PatientInformation.objects.filter(in_waiting_room=True)
    with open('waiting_list.csv', 'w', newline="") as waiting_list_csv:
        wr = csv.writer(waiting_list_csv, quoting=csv.QUOTE_ALL)
        if patients:
            wr.writerow(['First Name', 'Last Name', 'Age', 'Address', 'Uploaded', 'Story'])
            for patient in patients:
                wr.writerow([patient.first_name, patient.last_name, patient.age, patient.address, patient.uploaded,
                             patient.story])

        else:
            wr.writerows('')
        wr.writerow('')
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'waiting_list.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
@terms_required
def email_waiting_list(request):
    context['account'] = request.user
    if not request.user.group.name == 'Admin':
        return redirect('home')
    context['title'] = 'Email Waiting List'
    if request.POST:
        form = EmailForm(request.POST or None)
        if form.is_valid():
            to = request.POST.get('to')
            cc = request.POST.get('cc')
            bcc = request.POST.get('bcc')
            from_email = f"{request.user.first_name} {request.user.last_name} <contact@tvachacare.com>"
            title = str(request.POST.get('title'))
            message = request.POST.get('message')
            plain_text = str(message)
            to = to.split(',')
            cc = cc.split(',')
            bcc = bcc.split(',')
            html_message = render_to_string('waiting list/waiting_list_email.html',
                                            {'patients': PatientInformation.objects.filter(in_waiting_room=True),
                                             'message': message})
            email = EmailMessage(
                subject=title,
                body=html_message,
                to=to,
                cc=cc,
                bcc=bcc,
                from_email=from_email,
            )
            email.content_subtype = 'html'
            patients = PatientInformation.objects.filter(in_waiting_room=True)
            write_zipfile(request, patients)
            email.attach_file(os.path.join(BASE_DIR, 'media/patient_images.zip'))
            email.send()
            messages.add_message(request, messages.SUCCESS, 'Email sent successfully')
            return redirect('waiting_list')
    else:
        form = EmailForm()
    context['form'] = form
    context['different_fields'] = ['message']
    return render(request, 'generic_form_template.html', context)


def write_zipfile(request, patients):
    with ZipFile('media/patient_images.zip', 'w') as z:
        for patient in patients:
            if patient.patient_image:
                image_content = requests.get(request.build_absolute_uri(patient.patient_image.url)).content
                image_name = patient.patient_image.name
                zip_info = ZipInfo(filename=image_name)
                z.writestr(zip_info, image_content)
            if patient.injury_image:
                image_content = requests.get(request.build_absolute_uri(patient.injury_image.url)).content
                image_name = patient.injury_image.name
                zip_info = ZipInfo(filename=image_name)
                z.writestr(zip_info, image_content)
        z.close()


@login_required
@terms_required
def import_patients(request):
    context['account'] = request.user if request.user.is_authenticated else None

    if request.POST:
        file = request.FILES['csv_file'].read()
        error_dict = []
        with open('media/uploaded_template.csv', 'wb') as out:
            out.write(file)
        with open('media/uploaded_template.csv', 'r', newline='') as uploaded:
            reader = csv.DictReader(uploaded)
            for row in reader:
                row = {k.replace(' ', '_'): v for k, v in row.items()}
                row = {k.lower(): v for k, v in row.items()}
                form = AddPatient(row)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                else:
                    error_list = [error.as_text() for field, error in form.errors.items()]
                    error_dict.append(
                        {
                            'patient': f'{form.cleaned_data["first_name"]} {form.cleaned_data["last_name"]}',
                            'errors': error_list
                        }
                    )
        if error_dict:
            context['patients'] = error_dict
            return render(request, 'patients/csv_errors.html', context)
        else:
            messages.add_message(request, messages.SUCCESS, 'Patients Uploaded Successfully')

    return render(request, 'patients/csv_upload.html', context)


@login_required
@terms_required
def serve_import_template(request):
    def get_all_fields_from_form(instance):

        fields = list(instance().base_fields)

        for field in list(instance().declared_fields):
            if field not in fields:
                fields.append(field.replace('_', ' ').capitalize())
        fields = [field.replace('_', ' ').capitalize() for field in fields]
        return fields

    with open('media/patient_template.csv', 'w', newline='') as template:
        wr = csv.writer(template, quoting=csv.QUOTE_ALL)
        wr.writerow(get_all_fields_from_form(AddPatient))
    filepath = os.path.join(BASE_DIR, 'media/patient_template.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
@terms_required
def groups(request):
    context['account'] = request.user if request.user.is_authenticated else None
    context['groups'] = SurgeryGroup.objects.all()
    return render(request, 'groups/groups.html', context)


@login_required
@terms_required
def lock_unlock_group(request, group_id):
    if request.user.group.name != 'Admin':
        return redirect('groups')
    group = get_object_or_404(SurgeryGroup, id=group_id)
    group.locked = not group.locked
    group.save()
    next_page = request.GET.get('next')
    if next_page:
        return HttpResponseRedirect(next_page)
    return redirect('groups')


@login_required
@terms_required
def add_group(request):
    context['account'] = request.user if request.user.is_authenticated else None

    context['different_fields'] = []
    context['title'] = 'Add Group'

    if request.POST:
        form = SurgeryGroupForm(request.POST or None, error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, f'{obj.name} was created successfully')
            return redirect('groups')
    else:
        form = SurgeryGroupForm

    context['form'] = form

    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def edit_group(request, id):
    context['account'] = request.user if request.user.is_authenticated else None

    context['different_fields'] = []
    context['title'] = 'Edit Group'

    group = get_object_or_404(SurgeryGroup, id=id)

    if request.POST:
        form = SurgeryGroupForm(request.POST or None, error_class=DivErrorList, instance=group)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, f'{obj.name} was edited successfully')
            return redirect('groups')
    else:
        form = SurgeryGroupForm(instance=group)

    context['form'] = form

    return render(request, 'generic_form_template.html', context)


@login_required
@terms_required
def delete_group(request, id):
    context['account'] = request.user if request.user.is_authenticated else None
    group = get_object_or_404(SurgeryGroup, id=id)

    if request.POST:
        messages.success(request, f'{group.name} was deleted successfully')
        group.delete()
        return redirect('groups')

    context['title'] = 'Delete Group'
    context['objects'] = [group]
    return render(request, 'delete_object.html', context)


@login_required
@terms_required
def group_page(request, id):
    context['account'] = request.user if request.user.is_authenticated else None
    group = get_object_or_404(SurgeryGroup, id=id)
    context['group'] = group
    surgeries = try_sort_by(request.GET.get('sort-by'), context, SurgeryInformation, ['image', 'procedurecodes'],
                            group=group)
    context['object'] = surgeries

    surgery_tuple = []

    for surgeries in surgeries:
        try:
            surgery_tuple.append((surgeries, Image.objects.filter(surgery=surgeries)[0]))
        except IndexError:
            surgery_tuple.append((surgeries, None))
    context['surgeries'] = surgery_tuple

    return render(request, 'groups/group_page.html', context)


@login_required
@terms_required
def group_add_surgeries(request, id):
    context['account'] = request.user if request.user.is_authenticated else None
    group = get_object_or_404(SurgeryGroup, id=id)
    context['group'] = group
    surgeries_query = try_sort_by(request.GET.get('sort-by'), context, SurgeryInformation, ['image', 'procedurecodes'],
                                  reduce(operator.or_, [Q(group__exact=group), Q(group__exact=None)]))
    context['object'] = surgeries_query

    if request.POST:
        surgeries = request.POST.getlist('surgeries[]')
        if surgeries:
            surgery_inverse_query = [(~Q(id__exact=item) & Q(group__exact=group)) for item in surgeries]
            inverse_surgery_objects = SurgeryInformation.objects.filter(reduce(operator.and_, surgery_inverse_query))
            inverse_surgery_objects.update(group=None)
            surgery_query = [Q(id__exact=item) for item in surgeries]
            surgery_objects = SurgeryInformation.objects.filter(reduce(operator.or_, surgery_query))
            surgery_objects.update(group=group)

            surgery_string = ''
            for surgery in surgery_objects:
                surgery_string += f'Surgery #{str(surgery.id)}, '

            event_notes = f'{surgery_string[:len(surgery_string) - 2]} added to {group.name}'
            event = EventLog(event_type='Surgeries Added to Group', notes=event_notes, color='success',
                             icon='fas fa-plus')
            event.save()
        else:
            surgery_objects = SurgeryInformation.objects.filter(group=group)
            surgery_objects.update(group=None)
        next_page = request.GET.get('next')
        if next_page:
            return HttpResponseRedirect(next_page)
        return redirect('group_page', group.id)

    return render(request, 'groups/group_add_surgeries.html', context)


@login_required
@terms_required
def groups_bulk_approve(request, group_id):
    group = get_object_or_404(SurgeryGroup, id=group_id)
    surgeries = SurgeryInformation.objects.filter(group=group)
    if group.percent_completed() == 100:
        surgeries.update(is_approved=True, is_denied=False)

        event_notes = f'Surgeries Bulk Approved to Group \'{group.name}\''
        event = EventLog(event_type='Surgeries Bulk Approved', notes=event_notes, color='success',
                         icon='fas fa-plus')
        event.save()
        messages.success(request, 'Surgeries Successfully Bulk Approved')
    else:
        messages.error(request, 'Group Threshold Not Reached')
        return redirect('group_page', group.id)
    return redirect('groups')


@login_required
@terms_required
def activity(request):
    Account.objects.filter(id=request.user.id).update(unread_activity=0)

    context['account'] = request.user if request.user.is_authenticated else None

    events = EventLog.objects.all().order_by('-event_time')

    context['events'] = events

    return render(request, 'activity.html', context)


@login_required
@terms_required
def appeals(request):
    context['account'] = request.user
    context['appeals'] = Appeal.objects.all()
    request.user.unread_appeals = 0
    request.user.save()
    return render(request, 'appeals.html', context)


@login_required
@terms_required
def appeals_resolve(request, appeal_id):
    appeal = get_object_or_404(Appeal, id=appeal_id)
    appeal.delete()
    messages.success(request, 'Appeal Resolved Successfully')
    return redirect('appeals')

