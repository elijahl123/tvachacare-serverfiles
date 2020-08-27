import csv
import os

from django.contrib.auth import logout as lgout, authenticate, login
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.static import serve

from .forms import AccountAuthenticationForm, AccountUpdateForm, AddPatient, ImageForm, SurgeryForm, CSVForm
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

    if not request.user.is_authenticated:
        return redirect('login')

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
    if user.is_authenticated:
        return redirect("home")

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

    if request.user.is_authenticated:
        if request.user.group == 'Data Entry':
            return render(request, 'addPatient.html', context)
        elif request.user.is_superuser:
            return render(request, 'addPatient.html', context)
        else:
            return redirect('home')
    else:
        return redirect('login')
    '''
    if request.POST:
        form = AddPatient(request.POST)
        if form.is_valid():
            firstName = request.POST['firstName']
            lastName = request.POST['lastName']
            patientRecordNumber = request.POST['patientRecordNumber']
            preferredName = request.POST['preferredName']
            dateOfBirth = request.POST['dateOfBirth']
            ageAtSurgery = request.POST['ageAtSurgery']
            patientSex = request.POST['patientSex']
            siteCountry = request.POST['siteCountry']
            siteRegion = request.POST['siteRegion']
            hospitalName = request.POST['hospitalName']
            preoperativeDiagnostic1 = request.POST['preoperativeDiagnostic1']
            preoperativeDiagnostic2 = request.POST['preoperativeDiagnostic2']
            preoperativeDiagnostic3 = request.POST['preoperativeDiagnostic3']
            preoperativeDiagnostic4 = request.POST['preoperativeDiagnostic4']
            burnInjury = request.POST['burnInjury']
            TBSA = request.POST['TBSA']
            degreeOfBurn = request.POST['degreeOfBurn']
            causeOfBurn = request.POST['causeOfBurn']
            approximateYearOfInjury = request.POST['approximateYearOfInjury']
            occupation = request.POST['occupation']
            patientAddress = request.POST['patientAddress']
            patientPhoneNumber = request.POST['patientPhoneNumber']
            parentFirstName = request.POST['parentFirstName']
            parentMiddleName = request.POST['parentMiddleName']
            parentLastName = request.POST['parentLastName']
            relationshipToParent = request.POST['relationshipToParent']
            referral = request.POST['referral']
            patientWeight = request.POST['patientWeight']
            patientHeight = request.POST['patientHeight']
            currentMedication = request.POST['currentMedication']
            image1 = request.POST['image1']
            image2 = request.POST['image2']
            image3 = request.POST['image3']
            patient = authenticate(
                firstName=firstName, lastName=lastName, patientRecordNumber=patientRecordNumber,
                preferredName=preferredName, dateOfBirth=dateOfBirth, ageAtSurgery=ageAtSurgery,
                patientSex=patientSex, siteCountry=siteCountry, siteRegion=siteRegion, hospitalName=hospitalName,
                preoperativeDiagnostic1=preoperativeDiagnostic1, preoperativeDiagnostic2=preoperativeDiagnostic2,
                preoperativeDiagnostic3=preoperativeDiagnostic3, preoperativeDiagnostic4=preoperativeDiagnostic4,
                burnInjury=burnInjury, TBSA=TBSA, degreeOfBurn=degreeOfBurn, causeOfBurn=causeOfBurn,
                approximateYearOfInjury=approximateYearOfInjury, occupation=occupation, patientAddress=patientAddress,
                patientPhoneNumber=patientPhoneNumber, parentFirstName=parentFirstName,
                parentMiddleName=parentMiddleName,
                parentLastName=parentLastName, relationshipToParent=relationshipToParent,
                referral=referral, patientWeight=patientWeight, patientHeight=patientHeight,
                currentMedication=currentMedication,
                image1=image1, image2=image2, image3=image3)
            if patient:
                return redirect('home')
        else:
            form = AddPatient

        context['addpatient_form'] = form

    if request.user.is_authenticated:
        if request.user.group == 'Data Entry':
            return render(request, 'addPatient.html', context)
        else:
            return redirect('home')
    else:
        return redirect('login')
    '''


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
    context['patient'] = patient
    context['surgery'] = surgery
    if request.user.is_authenticated:
        return render(request, 'patient_page.html', context)
    else:
        return redirect('login')


def delete_patient(request, slug):
    if request.user.is_authenticated:
        patient = get_object_or_404(PatientInformation, slug=slug)
        patient.delete()
        return redirect('delete_images', slug=slug)
    else:
        return redirect('login')


def delete_images(request, slug):
    if request.user.is_authenticated:
        patient = PatientInformation.objects.filter(slug=slug)
        if patient:
            patient.delete()
            return redirect('home')
        else:
            return redirect('home')
    else:
        return redirect('login')


def approve_patient(request, slug):
    if request.user.is_authenticated:
        patient = get_object_or_404(PatientInformation, slug=slug)
        patient.is_approved = True
        patient.save()
        return redirect('home')
    else:
        return redirect('login')


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

    if request.user.is_authenticated:
        patient = get_object_or_404(PatientInformation, slug=slug)
        ImageFormSet = modelformset_factory(Image, form=ImageForm, extra=1)

        if request.method == 'POST':
            surgeryForm = SurgeryForm(request.POST)
            formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
            patient.is_approved = False
            patient.save()
            if surgeryForm.is_valid() and formset.is_valid():
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
    else:
        return redirect('login')


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
    if request.user.is_authenticated:
        return render(request, 'surgery_page.html', context)
    else:
        return redirect('login')


def delete_surgery(request, slug, id):
    if request.user.is_authenticated:
        surgery = get_object_or_404(SurgeryInformation, id=id)
        surgery.delete()
        return redirect('delete_images', slug=slug, id=id)
    else:
        return redirect('login')


def delete_surgery_images(request, slug, id):
    if request.user.is_authenticated:
        surgery = SurgeryInformation.objects.filter(id=id)
        if surgery:
            surgery.delete()
            return redirect('home')
        else:
            return redirect('home')
    else:
        return redirect('login')


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

    form = CSVForm(request.POST or None)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        write_response(date_start, date_end)
        return redirect('send_file')

    context['form'] = form

    if request.user.is_authenticated:
        return render(request, 'filter.html', context)
    else:
        return redirect('login')


def write_response(date_start, date_end):
    with open('filter.csv', 'w', newline="") as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        surgeries = SurgeryInformation.objects.filter(date_of_upload__range=[date_start, date_end]).values_list(
            'patient__gender',
            'patient__age',
            'patient__address',
            'patient__diagnosis',
            'cause_of_burn',
            'year_of_burn',
            'type_of_surgery',
            'date_of_surgery',
            'duration',
            'area_operated'
        )
        if surgeries:
            header = ['Gender', 'Age', 'Address', 'Diagnosis', 'Cause of Burn', 'Year of Burn', 'Type of Surgery',
                      'Date of Surgery', 'Duration', 'Area Operated']
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


def send_file(request):

    from pathlib import Path
    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    filepath = os.path.join(BASE_DIR, 'filter.csv')
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))

