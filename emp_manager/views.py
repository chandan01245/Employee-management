import os
import random

from bson import Binary
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.timezone import now

from .models import employee_details, login_details


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        response = login_details.find_one({'f_userName':username})
        if response and response['f_Pwd'] == password:
            request.session['logged_user'] = username
            return redirect("dashboard")
        return render(request,'login.html', {'error_message': "Please Enter Correct login credentials"})
    return render(request,'login.html')


def logout_page(request):
    user = request.session['logged_user']
    del request.session['logged_user']
    return render(request,'login.html',{'username':user})



def dashboard_page(request):
    username = request.session.get('logged_user', False)
    if username:
        return render(request,'dashboard.html',{'username':username})
    return redirect("login")


def employee_list(request):
    username = request.session.get('logged_user')
    if username:
        return render(request,'employee.html',{'username':username,'employees':employee_details.find({})})
    return redirect("login")


def create_employee(request):
    username = request.session.get('logged_user', False)
    if username:
        if request.method == 'POST':
            # Generate a unique ID
            max_employee = employee_details.find_one(sort=[("f_Id", -1)])  # Get the highest current ID
            newId = max_employee['f_Id'] + 1 if max_employee else 1

            # Format the current date
            formatted_date = now().strftime('%d-%b-%y')

            # Create a dictionary for employee data
            employee_data = {
                'f_Id': newId,
                'f_Createdate': formatted_date,
                'f_Name': request.POST.get('name'),
                'f_Image': None,  # Placeholder for the image to be uploaded
                'f_Email': request.POST.get('email'),
                'f_Mobile': request.POST.get('mobile'),
                'f_Designation': request.POST.get('designation'),
                'f_gender': request.POST.get('gender'),
                'f_Course': request.POST.getlist('course'),
            }

            image = request.FILES.get('image')
            if image:
                try:
                    # Convert the uploaded image file to binary
                    image_binary = Binary(image.read())

                    # Ensure `employee_data` is a dictionary and initialize `f_Image`
                    employee_data['f_Image'] = {
                        'filename': image.name,  # Original file name
                        'content_type': image.content_type,  # MIME type (e.g., 'image/jpeg')
                        'data': image_binary,  # Binary image data
                    }
                except Exception as e:
                    # Handle any exceptions (e.g., file read error)
                    print(f"Error while processing image: {e}")
                    # Optionally, log the error or return an appropriate response

            employee_details.insert_one(employee_data)
            return redirect("employee_list")
            # If the request method is not POST, render the form page again
        return render(request,'create_employee.html',{'username':username})
    return redirect("login")


def edit_employee(request,employee_id):
    username = request.session.get('logged_user', False)
    if username:
        if request.method == 'POST':
            # Fetch the existing employee data
            employee = employee_details.find_one({'f_Id': int(employee_id)})
            if not employee:
                return None

            # Create a dictionary to store the updated fields
            update_data = {}
            if request.POST.get('name'):
                update_data['f_Name'] = request.POST.get('name')
            if request.POST.get('email'):
                update_data['f_Email'] = request.POST.get('email')
            if request.POST.get('mobile'):
                update_data['f_Mobile'] = request.POST.get('mobile')
            if request.POST.get('designation'):
                update_data['f_Designation'] = request.POST.get('designation')
            if request.POST.get('gender'):
                update_data['f_gender'] = request.POST.get('gender')
            if request.POST.getlist('course'):
                update_data['f_Course'] = request.POST.getlist('course')

            # Handle the image upload
            image = request.FILES.get('image')
            if image:
                # Convert the uploaded image file to binary and prepare for MongoDB
                image_binary = Binary(image.read())
                update_data['f_Image'] = {
                    'filename': image.name,
                    'content_type': image.content_type,
                    'data': image_binary,
                }
            elif 'f_Name' in update_data and 'f_Image' in employee and employee['f_Image']:
                # Update only the image metadata if no new image is uploaded but name changes
                update_data['f_Image'] = employee['f_Image']
                # Ensure `filename` update is consistent with the new name
                file_extension = os.path.splitext(employee['f_Image']['filename'])[1]  # Get the file extension
                new_filename = f"{employee_id}-{update_data['f_Name'].replace(' ', '_')}{file_extension}"
                update_data['f_Image']['filename'] = new_filename
            # Update the employee data in the database
            if update_data:
                employee_details.update_one({'f_Id': int(employee_id)}, {'$set': update_data})

            return redirect("employee_list")
        employee = employee_details.find_one({'f_Id': int(employee_id)})
        if not employee:
            return HttpResponse("Employee not found", status=404)
        return render(request, 'update_employee.html', {'employee': employee,'username':username})
    return redirect("login")


def delete_employee(request, employee_id):
    result = employee_details.find_one({'f_Id': employee_id})
    if result:
        if result.get('f_Image'):
            # If the image is stored in MongoDB, ensure it's cleared from the database
            employee_details.update_one(
                {'f_Id': employee_id},
                {'$unset': {'f_Image': ""}}  # Remove the f_Image field
            )
        employee_details.delete_one({'f_Id': employee_id})
    return redirect("employee_list")
