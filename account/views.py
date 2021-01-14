import django.apps
from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404

from account.forms import *
from account.models import Account
from patientInformation.forms import *
from patientInformation.models import *
from patientInformation.views import terms_required

context = {'today': datetime.date.today()}


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
    account = request.user if request.user.is_authenticated else None
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
def admin_template(request, model):
    context['account'] = request.user
    model_dict = {}
    for model_obj in django.apps.apps.get_models():
        model_meta = model_obj._meta
        if slugify(
                model_meta.verbose_name_plural) == model and not (
                model_obj.__module__ == 'django.contrib.auth.models'):
            model_dict = {
                'model': slugify(model_meta.verbose_name_plural),
                'title': model_meta.verbose_name_plural,
                'items': model_obj.objects.all()
            }
            if model_obj.__module__ == 'account.models':
                from account import forms
            else:
                from patientInformation import forms
            if request.POST:
                if 'new_form_submit' in request.POST:
                    form = getattr(forms, model_obj.admin_form)(request.POST or None, request.FILES or None,
                                                                error_class=DivErrorList) or None
                    if form.is_valid():
                        obj = form.save(commit=False)
                        obj.save()
                        return redirect('admin_template', model)
                else:
                    form = getattr(forms, model_obj.admin_form)
                    delete_selected = request.POST.getlist('delete[]')
                    for item_id in delete_selected:
                        obj = model_obj.objects.get(id=int(item_id))
                        obj.delete()
                    return redirect('admin_template', model)
            else:
                form = getattr(forms, model_obj.admin_form)

            model_dict['new_form'] = form
    context['model'] = model_dict
    return render(request, 'admin_template.html', context)


@login_required
@terms_required
def admin_view(request, model, id):
    if not request.user.group.name == 'Admin':
        return redirect('home')
    account = request.user if request.user.is_authenticated else None
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
