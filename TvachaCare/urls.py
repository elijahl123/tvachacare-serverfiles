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

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include

from patientInformation import views

urlpatterns = [
    path('admin/', include('account.urls')),
    path('', views.index, name='home'),
    path('login/', views.loginPage, name="login"),
    path('login/admin/', views.loginadmin, name="loginAdmin"),
    path('addpatient/', views.addpatient, name='addPatient'),
    path('logout/', views.logout, name='logout'),
    path('patient/<slug>/', views.patient_page, name='patient_page'),
    path('patient/<slug>/delete-patient', views.delete_patient, name='delete_patient'),
    path('patient/<slug>/delete-images', views.delete_images, name='delete_images'),
    path('patient/<slug>/surgery/<id>/approve', views.approve_surgery, name='approve_surgery'),
    path('patient/<slug>/surgery/<id>/deny', views.deny_surgery, name='deny_surgery'),
    path('patient/<slug>/add-surgery', views.add_surgery, name='add_surgery'),
    path('patient/<slug>/surgery/<id>', views.surgery_page, name='surgery_page'),
    path('patient/<slug>/surgery/<id>/edit', views.edit_surgery, name='edit_surgery'),
    path('patient/<slug>/surgery/<surgery_id>/<image_id>/edit', views.edit_image, name='edit_image'),
    path('image/<image_id>/delete/', views.delete_image, name='delete_image'),
    path('patient/<slug>/surgery/<surgery_id>/add-image', views.add_image, name='add_image'),
    path('patient/<slug>/surgery/<id>/delete-surgery', views.delete_surgery, name='delete_surgery'),
    path('patient/<slug>/surgery/<id>/delete-surgery-images', views.delete_surgery_images,
         name='delete_surgery_images'),
    path('filter/', views.filter_by_date, name='filter_by_date'),
    path('hui-report/', views.hui_report, name='hui_report'),
    path('patient/edit/<slug>', views.edit_patient, name='edit_patient'),
    re_path(r'^filter.csv', views.send_file, name='send_file'),
    path('calendar/<year>/<current_month>', views.calendar_events, name='calendar'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('report-bug/', views.report_bug, name='report_bug'),
    path('waiting-list/', views.waiting_list, name='waiting_list'),
    path('waiting-list/search/', views.waiting_list_search, name='waiting_list_search'),
    path('waiting-list/add/<id>/', views.waiting_list_add, name='waiting_list_add'),
    path('waiting-list/remove/<id>/', views.waiting_list_remove, name='waiting_list_remove'),
    path('waiting-list/export/', views.export_waiting_list, name='export_waiting_list'),
    path('waiting-list/email/', views.email_waiting_list, name='email_waiting_list'),
    path('import-patients/', views.import_patients, name='import_patients'),
    path('import-patients/template/', views.serve_import_template, name='serve_import_template')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'patientInformation.views.error_404'

handler500 = 'patientInformation.views.error_500'
