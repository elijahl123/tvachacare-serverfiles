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
import os
from pathlib import Path

import requests
from django.conf import settings
from django.contrib.auth import logout as lgout, login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMessage, send_mail
from django.forms import formset_factory, model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.static import serve

from .forms import *
from .models import PatientInformation, Image, SurgeryInformation, Account, ProcedureCodes, EventLog, Group

context = {'today': datetime.date.today()}


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


@login_required
@terms_required
def add_surgery(request, slug):
    if not request.user.group.can_add_surgeries:
        return redirect('home')

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
@terms_required
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

    context['account'] = account

    if not request.user.group.can_add_patients:
        return redirect('home')

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

    return render(request, 'addPatient.html', context)


@login_required
@terms_required
def admin(request):
    if not request.user.group.name == 'Admin':
        return redirect('home')
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
    return render(request, 'admin.html', context)


@login_required
@terms_required
def admin_delete(request, model, id):
    if request.user.group.name != 'Admin':
        return redirect('admin-console')
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
    if model == 'accounts':
        item = get_object_or_404(Account, id=id)
        item.delete()
        return redirect('admin_template', 'accounts')
    elif model == 'groups':
        item = get_object_or_404(Group, id=id)
        item.delete()
        return redirect('admin_template', 'groups')
    elif model == 'event-logs':
        item = get_object_or_404(EventLog, id=id)
        item.delete()
        return redirect('admin_template', 'event-logs')
    elif model == 'patients':
        item = get_object_or_404(PatientInformation, id=id)
        item.delete()
        if PatientInformation.objects.filter(id=id).exists():
            return redirect('admin_delete', 'patients', id)
        else:
            return redirect('admin_template', 'patients')
    elif model == 'surgeries':
        item = get_object_or_404(SurgeryInformation, id=id)
        item.delete()
        if SurgeryInformation.objects.filter(id=id).exists():
            return redirect('admin_delete', 'surgeries', id)
        else:
            return redirect('admin_template', 'surgeries')
    else:
        return redirect('admin-console')


@login_required
@terms_required
def admin_edit(request, model, id):
    if not request.user.group.name == 'Admin':
        return redirect('home')
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
    model_dict = {'model': model}
    if model == 'accounts':
        model_dict['title'] = 'Accounts'
        model_dict['items'] = get_object_or_404(Account, id=id)
        if request.POST:
            form = AccountView(request.POST or None, request.FILES or None,
                               instance=get_object_or_404(Account, id=id), error_class=DivErrorList)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.save()
                return redirect('admin_template', 'accounts')
        else:
            form = AccountView(instance=get_object_or_404(Account, id=id))
        model_dict['form'] = form
    elif model == 'groups':
        model_dict['title'] = 'Groups'
        model_dict['items'] = get_object_or_404(Group, id=id)
        if request.POST:
            form = GroupForm(request.POST or None, instance=get_object_or_404(Group, id=id), error_class=DivErrorList)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.save()
                return redirect('admin_template', 'groups')
        else:
            form = GroupForm(instance=get_object_or_404(Group, id=id))
        model_dict['form'] = form
    elif model == 'event-logs':
        model_dict['title'] = 'Event Logs'
        model_dict['items'] = get_object_or_404(EventLog, id=id)
        if request.POST:
            form = EventLogForm(request.POST or None, instance=get_object_or_404(EventLog, id=id),
                                error_class=DivErrorList)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.save()
                return redirect('admin_template', 'event-logs')
        else:
            form = EventLogForm(instance=get_object_or_404(EventLog, id=id))
        model_dict['form'] = form
    elif model == 'patients':
        model_dict['title'] = 'Patients'
        model_dict['items'] = get_object_or_404(PatientInformation, id=id)
        if request.POST:
            form = AddPatient(request.POST or None, request.FILES or None,
                              instance=get_object_or_404(PatientInformation, id=id), error_class=DivErrorList)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.save()
                return redirect('admin_template', 'patients')
        else:
            form = AddPatient(instance=get_object_or_404(PatientInformation, id=id))
        model_dict['form'] = form
    elif model == 'surgeries':
        model_dict['title'] = 'Surgeries'
        model_dict['items'] = get_object_or_404(SurgeryInformation, id=id)
        if request.POST:
            form = SurgeryForm(request.POST or None, instance=get_object_or_404(SurgeryInformation, id=id),
                               error_class=DivErrorList)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.save()
                return redirect('admin_template', 'surgeries')
        else:
            form = SurgeryForm(instance=get_object_or_404(SurgeryInformation, id=id))
        model_dict['form'] = form
    else:
        return redirect('admin-console')
    context['model'] = model_dict
    return render(request, 'admin_edit.html', context)


@login_required
@terms_required
def admin_template(request, model: str):
    if not request.user.group.name == 'Admin':
        return redirect('home')
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
    model_dict = {'model': model}
    if model == 'accounts':
        model_dict['title'] = 'Accounts'
        model_dict['items'] = Account.objects.all()
        if request.POST:
            if 'new_form_submit' in request.POST:
                form = RegistrationForm(request.POST or None, error_class=DivErrorList)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    form = RegistrationForm()
                    return redirect('admin_template', 'accounts')
            else:
                form = RegistrationForm()
                delete_selected = request.POST.getlist('delete[]')
                for item_id in delete_selected:
                    obj = Account.objects.get(id=int(item_id))
                    obj.delete()
                return redirect('admin_template', 'accounts')
        else:
            form = RegistrationForm()
        model_dict['new_form'] = form
    elif model == 'groups':
        model_dict['title'] = 'Groups'
        model_dict['items'] = Group.objects.all()
        model_dict['accounts'] = Account.objects.all()
        if request.POST:
            if 'new_form_submit' in request.POST:
                form = GroupForm(request.POST or None, error_class=DivErrorList)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    form = GroupForm()
                    return redirect('admin_template', 'groups')
            else:
                form = GroupForm()
                delete_selected = request.POST.getlist('delete[]')
                for item_id in delete_selected:
                    obj = Group.objects.get(id=int(item_id))
                    obj.delete()
                return redirect('admin_template', 'groups')
        else:
            form = GroupForm()
        model_dict['new_form'] = form
    elif model == 'event-logs':
        model_dict['title'] = 'Event Logs'
        model_dict['items'] = EventLog.objects.all().order_by('-event_time')
        if request.POST:
            if 'new_form_submit' in request.POST:
                form = EventLogForm(request.POST or None, error_class=DivErrorList)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    form = EventLogForm()
                    return redirect('admin_template', 'event-logs')
            else:
                form = EventLogForm()
                delete_selected = request.POST.getlist('delete[]')
                for item_id in delete_selected:
                    obj = EventLog.objects.get(id=int(item_id))
                    obj.delete()
                return redirect('admin_template', 'event-logs')
        else:
            form = EventLogForm()
        model_dict['new_form'] = form
    elif model == 'patients':
        model_dict['title'] = 'Patients'
        model_dict['items'] = PatientInformation.objects.all()
        if request.POST:
            if 'new_form_submit' in request.POST:
                form = AddPatient(request.POST or None, request.FILES or None, error_class=DivErrorList)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    form = AddPatient()
                    return redirect('admin_template', 'patients')
            else:
                form = AddPatient()
                delete_selected = request.POST.getlist('delete[]')
                for item_id in delete_selected:
                    obj = PatientInformation.objects.get(id=int(item_id))
                    obj.delete()
                return redirect('admin_template', 'patients')
        else:
            form = AddPatient()
        model_dict['new_form'] = form
    elif model == 'surgeries':
        model_dict['title'] = 'Surgeries'
        model_dict['items'] = SurgeryInformation.objects.all()
        if request.POST:
            if 'new_form_submit' in request.POST:
                form = SurgeryForm(request.POST or None, error_class=DivErrorList)
                if form.is_valid():
                    surgery_form = form.save(commit=False)
                    surgery_form.save()
                    images = request.FILES.getlist('surgery_images')
                    procedure_codes = request.POST.getlist('procedure_codes')
                    for image in images:
                        image_object = Image(surgery=surgery_form, image=image,
                                             date_of_upload_image=datetime.date.today())
                        image_object.save()
                    for code in procedure_codes:
                        procedure_code = ProcedureCodes(surgery=surgery_form, procedure_codes=code)
                        procedure_code.save()
                    return redirect('admin_template', 'surgeries')
            else:
                form = SurgeryForm()
                delete_selected = request.POST.getlist('delete[]')
                for item_id in delete_selected:
                    obj = SurgeryInformation.objects.get(id=int(item_id))
                    obj.delete()
                return redirect('admin_template', 'surgeries')
        else:
            form = SurgeryForm()
        model_dict['new_form'] = form
    else:
        return redirect('admin-console')
    context['model'] = model_dict
    return render(request, 'admin_template.html', context)


@login_required
@terms_required
def admin_view(request, model, id):
    if not request.user.group.name == 'Admin':
        return redirect('home')
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
    model_dict = {'model': model}
    if model == 'accounts':
        model_dict['title'] = 'Accounts'
        model_dict['item'] = AccountView(data=model_to_dict(get_object_or_404(Account, id=id)))
        account_model = Account.objects.get(id=id)
        context['user'] = account_model
    elif model == 'groups':
        model_dict['title'] = 'Groups'
        model_dict['item'] = GroupForm(data=model_to_dict(get_object_or_404(Group, id=id)))
    elif model == 'event-logs':
        model_dict['title'] = 'Event Logs'
        model_dict['item'] = EventLogForm(data=model_to_dict(get_object_or_404(EventLog, id=id)))
    elif model == 'patients':
        model_dict['title'] = 'Patients'
        model_dict['item'] = PatientView(data=model_to_dict(get_object_or_404(PatientInformation, id=id)))
        context['patient'] = get_object_or_404(PatientInformation, id=id)
    elif model == 'surgeries':
        model_dict['title'] = 'Surgeries'
        model_dict['item'] = SurgeryForm(data=model_to_dict(get_object_or_404(SurgeryInformation, id=id)))
        context['images'] = Image.objects.filter(surgery=id)
        context['procedure_codes'] = ProcedureCodes.objects.filter(surgery=id)
    else:
        return redirect('admin-console')
    context['model'] = model_dict
    return render(request, 'admin_view.html', context)


@login_required
@terms_required
def approve_surgery(request, slug, id):
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.is_approved = True
    surgery.is_denied = False
    surgery.save()
    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Approved'
    event = EventLog(user=request.user.email, event_type='Surgery Approved', notes=event_notes)
    event.save()
    return redirect('home')


@login_required
@terms_required
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
    else:
        return redirect('home')


@login_required
@terms_required
def delete_patient(request, slug):
    patient = get_object_or_404(PatientInformation, slug=slug)
    event_notes = 'Patient ID #' + str(patient.id) + ' was Deleted'
    event = EventLog(user=request.user.email, event_type='Patient Deleted', notes=event_notes)
    event.save()
    patient.delete()
    return redirect('delete_images', slug=slug)


@login_required
@terms_required
def delete_surgery(request, slug, id):
    surgery = get_object_or_404(SurgeryInformation, id=id)
    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Deleted'
    event = EventLog(user=request.user.email, event_type='Surgery Deleted', notes=event_notes)
    event.save()
    surgery.delete()
    return redirect('delete_surgery_images', slug=slug, id=id)


@login_required
@terms_required
def delete_surgery_images(request, slug, id):
    surgery = SurgeryInformation.objects.filter(id=id)
    if surgery:
        surgery.delete()
        return redirect('patient_page', slug)
    else:
        return redirect('patient_page', slug)


@login_required
@terms_required
def deny_surgery(request, slug, id):
    surgery = get_object_or_404(SurgeryInformation, id=id)
    surgery.is_denied = True
    surgery.is_approved = False
    surgery.save()
    event_notes = 'Surgery ID #' + str(surgery.id) + ' was Denied'
    event = EventLog(user=request.user.email, event_type='Surgery Denied', notes=event_notes)
    event.save()
    return redirect('home')


@login_required
@terms_required
def edit_patient(request, slug):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
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

    context['form'] = form
    context['patient'] = patient
    return render(request, 'editPatient.html', context)


@login_required
@terms_required
def filter_by_date(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
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
        print(fields)
        event_notes = 'Filter.csv was created'
        event = EventLog(user=request.user.email, event_type='Filter Created', notes=event_notes)
        event.save()
        if not request.POST.get('procedure_codes'):
            write_response(date_start, date_end, fields)
        else:
            write_response(date_start, date_end, fields, procedure_code_boolean=True)

        return redirect('send_file')

    context['form'] = form

    return render(request, 'filter.html', context)


@login_required
@terms_required
def hui_report(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
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
        event = EventLog(user=request.user.email, event_type='Report Created', notes=event_notes)
        event.save()
        write_response(date_start, date_end, fields, procedure_code_boolean=True)

        return redirect('send_file')

    context['form'] = form

    return render(request, 'hui_filter.html', context)


@login_required
@terms_required
def index(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        'group': request.user.group,
        'is_superuser': request.user.is_superuser
    } if request.user.is_authenticated else None

    context['account'] = account
    if request.user.is_authenticated:
        if request.user.group.can_approve:
            surgery = SurgeryInformation.objects.all()
            context['object'] = surgery
        else:
            patient = PatientInformation.objects.all()
            surgery = SurgeryInformation.objects.all()
            context['object'] = patient
            context['surgery'] = surgery

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

    return render(request, 'index.html', context)


def loginadmin(request):
    user = request.user

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
            result_json = resp.json()

            print(result_json)
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                event = EventLog(user=email, event_type='Login', notes='Logged In')
                event.save()
                if user.is_accepted:
                    if request.GET.get('next'):
                        return HttpResponseRedirect(request.GET.get('next'))
                    else:
                        return redirect('home')
                else:
                    return redirect('terms_of_service')
        else:
            email = request.POST['email'] or None

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            event = EventLog(user=email, event_type='Failed Login', notes='Failed Login Attempt from ' + ip)
            event.save()

    else:
        form = AccountAuthenticationForm()

    context['login_form'] = form
    return render(request, 'loginAdmin.html', context)


def loginPage(request):
    return render(request, 'login.html', {'groups': Group.objects.all()})


@login_required
def logout(request):
    event_notes = 'Logged Out'
    event = EventLog(user=request.user.email, event_type='Logged Out', notes=event_notes)
    event.save()
    lgout(request)
    return redirect("login")


@login_required
@terms_required
def patient_page(request, slug):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
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

    context['form'] = form
    context['patient'] = patient
    context['surgery'] = surgery
    return render(request, 'patient_page.html', context)


def privacyPolicy(request):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
    return render(request, 'privacyPolicy.html', context)


@login_required
@terms_required
def send_file(request):
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'filter.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
@terms_required
def surgery_page(request, slug, id):
    account = {
        "id": request.user.id,
        "name": request.user.username,
        "email": request.user.email,
        "is_superuser": request.user.is_superuser,
        "group": request.user.group,
    } if request.user.is_authenticated else None
    context['account'] = account
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
            to_emails = Account.objects.filter(group__name='Approver').values_list('email', flat=True)
            message = request.POST.get('appeal_request')
            html_message = render_to_string('appeal_email.html',
                                            {'patient': patient, 'account': account, 'message': message,
                                             'surgery': surgery})
            for email in to_emails:
                send_mail(subject, message, from_email='Appeal Request <contact@tvachacare.com>',
                          recipient_list=[email],
                          html_message=html_message)

    return render(request, 'surgery_page.html', context)


def terms_of_service(request):
    if request.POST:
        if 'accept' in request.POST:
            account = get_object_or_404(Account, id=request.user.id)
            account.is_accepted = True
            account.save()
            if 'next' in request.GET:
                return HttpResponseRedirect(request.GET.get('next'))
            else:
                return redirect('home')
        else:
            return redirect('logout')

    return render(request, 'terms_of_service.html', context)


@login_required
@terms_required
def add_image(request, slug, surgery_id):
    context['account'] = request.user
    context['title'] = 'Add Image'
    if request.POST:
        form = AddImage(request.POST or None, request.FILES or None)
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
def edit_surgery(request, slug, id):
    context['account'] = request.user
    if request.POST:
        form = SurgeryForm(request.POST or None, instance=get_object_or_404(SurgeryInformation, id=id))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return redirect('surgery_page', slug, id)
    else:
        form = SurgeryForm(instance=get_object_or_404(SurgeryInformation, id=id))
    context['form'] = form
    surgery = get_object_or_404(SurgeryInformation, id=id)
    context['surgery'] = surgery
    context['images'] = Image.objects.filter(surgery=surgery)
    return render(request, 'edit_surgery.html', context)


@login_required
@terms_required
def edit_image(request, slug, surgery_id, image_id):
    context['account'] = request.user
    context['title'] = 'Edit Image'
    if request.POST:
        form = ImageForm(request.POST or None, request.FILES or None, instance=get_object_or_404(Image, id=image_id))
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
