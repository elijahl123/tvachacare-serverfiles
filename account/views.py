import django.apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify

from account.forms import *
from patientInformation.forms import *
from patientInformation.models import *
from patientInformation.views import terms_required

context = {'today': datetime.date.today()}


@login_required
@terms_required
def admin(request):
    """
    Admin view for the console home that displays the list of object types in the database
    """
    if not request.user.group.name == 'Admin':
        return redirect('home')
    account = request.user if request.user.is_authenticated else None
    context['account'] = account
    return render(request, 'admin/admin.html', context)


@login_required
@terms_required
def admin_delete(request, model, id):
    """
    Admin Delete Function that retrieves the object and deletes it or returns a 404 error if the object is not found
    """
    if request.user.group.name != 'Admin':
        return redirect('admin-console')
    account = request.user if request.user.is_authenticated else None
    context['account'] = account
    if model == 'accounts':
        item = get_object_or_404(Account, id=id)
        item.delete()
        return redirect('admin_template', 'accounts')
    if model == 'groups':
        item = get_object_or_404(Group, id=id)
        item.delete()
        return redirect('admin_template', 'groups')
    if model == 'patients':
        item = get_object_or_404(PatientInformation, id=id)
        item.delete()
        if PatientInformation.objects.filter(id=id).exists():
            return redirect('admin_delete', 'patients', id)
        return redirect('admin_template', 'patients')
    if model == 'surgeries':
        item = get_object_or_404(SurgeryInformation, id=id)
        item.delete()
        if SurgeryInformation.objects.filter(id=id).exists():
            return redirect('admin_delete', 'surgeries', id)
        return redirect('admin_template', 'surgeries')
    return redirect('admin-console')


@login_required
@terms_required
def admin_edit(request, model, id):
    """
    Admin Edit Function that retrieves the object from the database and presents the proper form in which to edit that
    instance of the object
    """
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
    return render(request, 'admin/admin_edit.html', context)


@login_required
@terms_required
def admin_template(request, model):
    """
    Admin Template displays a list of the objects corresponding to a specific item group (ex. Surgeries, Patients, etc.)
    """
    context['account'] = request.user if request.user.is_authenticated else None
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
    return render(request, 'admin/admin_template.html', context)


@login_required
@terms_required
def admin_view(request, model, id):
    """
    Admin View function retrieves information on a specific object from an item group and displays all the form
    information attached to it
    """
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
    return render(request, 'admin/admin_view.html', context)


account_page_list = [
    ('/account', 'fas fa-user-edit', 'Edit Profile'),
]


@login_required
@terms_required
def account(request):
    """
    Displays the Account Homepage, which by default displays a form for the user to change their account information
    """
    context['account'] = request.user if request.user.is_authenticated else None

    context['account_page_list'] = account_page_list
    context['account_page_title'] = 'Edit Profile'

    if request.POST:
        form = AccountUpdateForm(request.POST or None, request.FILES or None, instance=request.user,
                                 error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, 'Account changed successfully')
            return redirect('account')
    else:
        form = AccountUpdateForm(instance=request.user)

    context['form'] = form

    return render(request, 'account/account.html', context)


@login_required
@terms_required
def change_password(request):
    """
    Displays a form with the form template where the user can change their password.
    """
    context['account'] = request.user if request.user.is_authenticated else None
    context['different_fields'] = []
    context['title'] = 'Change Password'

    if request.POST:
        form = ChangePasswordForm(request.POST or None, request.FILES or None, instance=request.user,
                                  error_class=DivErrorList)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, 'Account changed successfully')
            return redirect('account')
    else:
        form = ChangePasswordForm(instance=request.user)

    context['form'] = form

    return render(request, 'generic_form_template.html', context)
