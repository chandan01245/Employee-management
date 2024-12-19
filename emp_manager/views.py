import os
import random

from bson import Binary
from bson.objectid import ObjectId
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
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
            response = redirect("dashboard")
            response.set_cookie('username', username, max_age=3)
            return response
        else:
            messages.error(request,("Invalid password. PLease try again"))
            return render(request,'login.html')
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
        # Convert MongoDB cursor to a list and ensure _id is a string
        employees = list(employee_details.find())
        for employee in employees:
            employee['_id'] = str(employee['_id'])
        paginator = Paginator(employees, 1)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'employee.html', {'username': username,'page_obj': page_obj})
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
                redirect("employee_list")
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
            redirect("employee_list")
        return render(request, 'update_employee.html', {'employee': employee,'username':username})
    return redirect("login")


def delete_employee(request, employee_id):
    result = employee_details.find_one({'f_Id': int(employee_id)})
    if result:
        if result.get('f_Image'):
            # If the image is stored in MongoDB, ensure it's cleared from the database
            employee_details.update_one(
                {'f_Id': employee_id},
                {'$unset': {'f_Image': ""}}  # Remove the f_Image field
            )
        employee_details.delete_one({'f_Id': int(employee_id)})
    return redirect("employee_list")

def serve_image(request, employee_id):
    # Find the employee by their f_Id
    employee = employee_details.find_one({'f_Id': int(employee_id)})

    if not employee or 'f_Image' not in employee or not employee['f_Image']:
        # Return a default image or 404 if no image is found
        return HttpResponse("Image not found", content_type="text/plain", status=404)

    # Extract image data and metadata
    image_data = employee['f_Image']['data']
    content_type = employee['f_Image']['content_type']

    # Return the image in the response
    return HttpResponse(image_data, content_type=content_type)

def check_email_duplicate(request):
    email = request.GET.get('email')
    # Check for email existence in MongoDB
    exists = employee_details.find_one({"f_Email": email}) is not None
    return JsonResponse({'exists': exists})