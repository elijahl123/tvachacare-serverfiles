from django.contrib.auth import logout as lgout, authenticate, login
from django.shortcuts import render, redirect, get_object_or_404

from .forms import AccountAuthenticationForm, AccountUpdateForm, AddPatient
from .models import PatientInformation


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
        'group': request.user.group,
    } if request.user.is_authenticated else None
    context = {
        "account": account,
    }

    form = AddPatient(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.save()
        form = AddPatient()
        return redirect('home')

    context['form'] = form

    if request.user.is_authenticated:
        if request.user.group == 'Data Entry':
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
    context['patient'] = patient
    if request.user.is_authenticated:
        return render(request, 'patient_page.html', context)
    else:
        return redirect('login')
