from flask import Flask, render_template, request, session, Response, jsonify, redirect
from pymysql import connections
import os
import boto3
import datetime
import base64
from config import *
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = "CC"

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

@app.route('/')
def index():
    return render_template('home.html', number=1)

@app.route('/logoutCompany')
def logoutCompany():  
    if 'id' in session:  
        session.pop('logedInCompany',None)  
        return render_template('home.html')  
    else:  
        return render_template('home.html') 

@app.route('/logoutAdmin')
def logoutAdmin():  
    if 'id' in session:  
        session.pop('logedInAdmin',None)  
        return render_template('home.html')
    else:  
        return render_template('home.html')

@app.route('/register_company')
def register_company():
    return render_template('RegisterCompany.html')

@app.route('/publish_job')
def publish_job():
    data_company = passCompSession().get_json()
    comp_name = data_company.get('comp_name', '')
    return render_template('PublishJob.html', name=comp_name)

@app.route('/companyViewApplication', methods=['POST'])
def companyViewApplication():
    data_company = passCompSession().get_json()
    comp_name = data_company.get('comp_name', '')
    # return render_template('ViewCompanyApplication.html', name=comp_name)

# def getCompanyJobApplication():
    # action=request.form['action']
    currentCompany=str(session['logedInCompany'])
    select_sql = f"SELECT * FROM companyApplication ca JOIN job j ON ca.job = j.jobId WHERE j.company = '%{id}%'"
    cursor = db_conn.cursor()

    # if action == 'drop':
    #     select_sql = f"SELECT * FROM companyApplication ca JOIN job j ON ca.job = j.jobId WHERE j.company = '%{id}%'"
    #     cursor = db_conn.cursor()

    # if action =='pickUp':
    #     select_sql = f"SELECT * FROM companyApplication ca JOIN job j ON ca.job = j.jobId WHERE j.company = '%{id}%'"
    #     cursor = db_conn.cursor()

    try:
        print(currentCompany)
        cursor.execute(select_sql, (currentCompany,))
        jobApplication = cursor.fetchall()  # Fetch all students

        company_application_list = []
        print(application[0])
        for application in jobApplication:
            applicationId = application[0]
            applicationDateTime = application[1]
            applicationStatus = application[2]

            select_sql = f"SELECT s.studentId, s.studentName, s.mobileNumber, s.gender, s.address, s.email, s.level, s.programme FROM student s JOIN companyApplication ca ON s.studentId = ca.student WHERE ca.applicationId = '%{id}%'"
            cursor = db_conn.cursor()
            cursor.execute(select_sql, (applicationId,))
            studentInfo = cursor.fetchall()
            
            stud_id = studentInfo[0]
            stud_name = studentInfo[1]
            stud_phone = studentInfo[2]
            stud_gender = studentInfo[3]
            stud_address = studentInfo[4]
            stud_email = studentInfo[5]
            stud_level = studentInfo[6]
            stud_programme = studentInfo[7]
            stud_cohort = studentInfo[8]
            
            # Construct the S3 object key
            object_key = f"{stud_id}_resume"

            # Generate a presigned URL for the S3 object
            s3_client = boto3.client('s3')

            try:
                response = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': custombucket,
                        'Key': object_key,
                        'ResponseContentDisposition': 'inline',
                    },
                    ExpiresIn=3600  # Set the expiration time (in seconds) as needed
                )
            except ClientError as e:
                return str(e)
                # if e.response['Error']['Code'] == 'NoSuchKey':
                #     # If the resume does not exist, return a page with a message
                #     return render_template('home.html')
                # else:
                #     return str(e)
                
            application_data = {
                    "application_id" : applicationId,
                    "application_datetime" : applicationDateTime,
                    "application_status" : applicationStatus,
                    "student_id": stud_id,
                    "stud_name": stud_name,
                    "stud_phone": stud_phone,
                    "stud_gender": stud_gender,
                    "stud_address": stud_address,
                    "stud_email": stud_email,
                    "stud_level": stud_level,
                    "stud_programme": stud_programme,
                    "stud_cohort": stud_cohort,
                    "stud_resume": response,
                }

            # Append the student's dictionary to the student_list
            print(applicationId)
            company_application_list.append(application_data)
         
        # if action == 'drop':
        #  return render_template('DropStudent.html', application_list=company_application_list,id=id)

        # if action =='pickUp': 
        #  return render_template('PickUpStudent.html', application_list=company_application_list)
        return render_template('ViewCompanyApplication.html',name=comp_name, applicationData = company_application_list)
    except Exception as e:
        return str(e)

    finally:
        cursor.close()



@app.route('/companyViewManageJob')
def companyViewManageJob():
    data_company = passCompSession().get_json()
    comp_name = data_company.get('comp_name', '')
    return render_template('CompanyViewManageJob.html', name=comp_name)

@app.route('/login_company')
def login_company():
    return render_template('LoginCompany.html')

def passCompSession():
    currentCompany = str(session['logedInCompany'])
    select_sql = "SELECT * FROM company WHERE companyId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (currentCompany,))
        company = cursor.fetchone()

        return jsonify({
        'comp_name': company[2],
        'comp_about': company[3],
        'comp_address': company[4],
        'comp_email': company[5],
        'comp_phone': company[6]
        })
            
    except Exception as e:
        print(str(e))

    finally:
        cursor.close()

@app.route('/updateCompanyPassword', methods=['POST'])
def updateCompanyPassword():
    currentCompany = str(session['logedInCompany'])
    password = request.form['new_password']
    
    update_sql = "UPDATE company SET password=%s WHERE companyId=%s"
    cursor = db_conn.cursor()

    try:
        # Check if the company exists
        check_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor.execute(check_sql, (currentCompany,))
        existing_company = cursor.fetchone()

        if not existing_company:
            return "Company not found"
        
        cursor.execute(update_sql, (password, int(currentCompany)))
        db_conn.commit()

    finally:
        cursor.close()
        print("Company password updated successfully...")

        # Reload page with updated company profile
        currentCompany = str(session['logedInCompany'])
        select_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (currentCompany,))
            company = cursor.fetchone()

            if not company:
                print("company not found")

            comp_name = company[2]
            comp_about = company[3]
            comp_address = company[4]
            comp_email = company[5]
            comp_phone = company[6]

            # Fetch the S3 image URL based on comp_id
            comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': comp_image_file_name_in_s3},
                                                    ExpiresIn=7400)  # Adjust the expiration time as needed            
                return render_template('EditCompanyProfile.html', name=comp_name, compName=comp_name, compLogo=response, compAbout=comp_about, compAddress=comp_address, compEmail=comp_email, compPhone=comp_phone)
                
            except Exception as e:
                print(str(e))

        except Exception as e:
            print(str(e))

        finally:
            cursor.close()

@app.route("/updateCompanyProfile", methods=['POST'])
def updateCompanyProfile():
    currentCompany = str(session['logedInCompany'])
    companyName = request.form['company_name']
    companyAbout = request.form['about_company']
    companyPhone = request.form['company_phone']
    companyEmail = request.form['company_email']
    companyAddress = request.form['company_address']
    company_image_file = request.files['company_image_file']

    update_sql = "UPDATE company SET name=%s, about=%s, phone=%s, email=%s, address=%s WHERE companyId=%s"
    cursor = db_conn.cursor()
    
    try:
        # Check if the company exists
        check_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor.execute(check_sql, (currentCompany,))
        existing_company = cursor.fetchone()

        if not existing_company:
            return "Company not found"
        
        cursor.execute(update_sql, (companyName, companyAbout, companyPhone, companyEmail, companyAddress, int(currentCompany)))
        db_conn.commit()
        
        if company_image_file.filename != "" : 
            # Update image file in S3
            comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
            s3 = boto3.resource('s3')

            try:
                print("Updating company profile...")
                s3.Bucket(custombucket).put_object(Key=comp_image_file_name_in_s3, Body=company_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location.get('LocationConstraint'))

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    comp_image_file_name_in_s3)

            except Exception as e:
                return str(e)
            
    finally:
        cursor.close()
        print("Company profile updated successfully...")
        
        # Reload page with updated company profile
        currentCompany = str(session['logedInCompany'])
        select_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (currentCompany,))
            company = cursor.fetchone()

            if not company:
                print("company not found")

            comp_name = company[2]
            comp_about = company[3]
            comp_address = company[4]
            comp_email = company[5]
            comp_phone = company[6] 

            # Fetch the S3 image URL based on comp_id
            comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': comp_image_file_name_in_s3},
                                                    ExpiresIn=7400)  # Adjust the expiration time as needed            
                return render_template('EditCompanyProfile.html', name=comp_name, compName=comp_name, compLogo=response, compAbout=comp_about, compAddress=comp_address, compEmail=comp_email, compPhone=comp_phone)
                
            except Exception as e:
                print(str(e))

        except Exception as e:
            print(str(e))

        finally:
            cursor.close()
        
@app.route('/manage_company_profile')
def manage_company_profile():
    currentCompany = str(session['logedInCompany'])
    select_sql = "SELECT * FROM company WHERE companyId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (currentCompany,))
        company = cursor.fetchone()

        if not company:
            print("company not found")

        comp_name = company[2]
        comp_about = company[3]
        comp_address = company[4]
        comp_email = company[5]
        comp_phone = company[6] 

        # Fetch the S3 image URL based on comp_id
        comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
        s3 = boto3.client('s3')
        bucket_name = custombucket

        try:
            response = s3.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name,
                                                         'Key': comp_image_file_name_in_s3},
                                                 ExpiresIn=7400)  # Adjust the expiration time as needed            
            return render_template('EditCompanyProfile.html', name=comp_name, compName=comp_name, compLogo=response, compAbout=comp_about, compAddress=comp_address, compEmail=comp_email, compPhone=comp_phone)
            
        except Exception as e:
            print(str(e))

    except Exception as e:
        print(str(e))

    finally:
        cursor.close()
        
@app.route('/login_admin')
def login_admin():
    return render_template('LoginAdmin.html')

@app.route("/addCompanyReg", methods=['POST'])
def addCompanyRegistration():
    try:
        # Create a cursor
        cursor = db_conn.cursor()
        
        # Execute the SELECT COUNT(*) query to get the total row count
        select_sql = "SELECT COUNT(*) as total FROM company"      
        cursor.execute(select_sql)
        result = cursor.fetchone()
        
        cursor.close()

        company_id = int(result[0]) + 1
        company_name = request.form['company_name']
        company_image_file = request.files['company_image_file']
        about_company = request.form['about_company']
        company_phone = request.form['company_phone']
        company_address = request.form['company_address']
        company_email = request.form['company_email']
        password = request.form['password']

        insert_sql = "INSERT INTO company VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if company_image_file.filename == "":
            return "Please select a file"
        
        try:
                cursor.execute(insert_sql, (company_id, password, company_name, about_company, company_address, company_email, company_phone, "pending",))
                db_conn.commit()
                
                # Uplaod image file in S3 #
                comp_image_file_name_in_s3 = "comp-id-" + str(company_id) + "_image_file"
                s3 = boto3.resource('s3')

                try:
                    print("Data inserted in MySQL RDS... uploading image to S3...")
                    s3.Bucket(custombucket).put_object(Key=comp_image_file_name_in_s3, Body=company_image_file)
                    bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                    s3_location = (bucket_location['LocationConstraint'])

                    if s3_location is None:
                        s3_location = ''
                    else:
                        s3_location = '-' + s3_location

                    object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                        s3_location,
                        custombucket,
                        comp_image_file_name_in_s3)

                except Exception as e:
                    return str(e)
        
        finally:
            cursor.close()
            print("Company registration request submitted...")
            return render_template('home.html')
    
    except Exception as e:
        print(str(e))
        print("failed get count...")
        return render_template('home.html')
    
@app.route("/addJob", methods=['POST'])
def addJob():
    try:
        # Create a cursor
        cursor = db_conn.cursor()
        
        # Execute the SELECT COUNT(*) query to get the total row count
        select_sql = "SELECT COUNT(*) as total FROM job"      
        cursor.execute(select_sql)
        result = cursor.fetchone()
        
        cursor.close()
        current_datetime = datetime.datetime.now()

        # Format the date as a string (e.g., "2023-09-09 10:15:30")
        job_id = int(result[0]) + 1
        publish_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')       
        job_type = request.form['job_type']
        job_position = request.form['job_position']
        qualification_level = request.form['qualification_level']
        job_description = request.form['job_description']
        job_requirement = request.form['job_requirement']
        job_location = request.form['job_location']
        job_salary = request.form['job_salary']
        job_openings = request.form['job_openings']       
        job_industry = request.form['job_industry']
        company = int(session['logedInCompany'])

        insert_sql = "INSERT INTO job VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        try:
            cursor.execute(insert_sql, (job_id, publish_date, job_type, job_position, qualification_level, job_description, job_requirement, job_location, job_salary, job_openings, company, job_industry,))
            db_conn.commit()
               
        except Exception as e:
                print(str(e))

    except Exception as e:
                print(str(e))

    finally:
        cursor.close()
        print("Job published...")
        data_company = passCompSession().get_json()
        comp_name = data_company.get('comp_name', '')
        return render_template('ViewCompanyApplication.html', name=comp_name)
    
@app.route("/loginCompany", methods=['GET','POST'])
def loginCompany():
    if request.method == 'POST':
        email = request.form['company_email']
        password = request.form['password']

        select_sql = "SELECT * FROM company WHERE email = %s AND password = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (email,password,))
            company = cursor.fetchone()
            
            if company: 
                if company[7] != 'pending': 
                    session['logedInCompany'] = str(company[0])

                    currentCompany=str(session['logedInCompany'])
                    select_sql = f"SELECT * FROM companyApplication ca JOIN job j ON ca.job = j.jobId WHERE j.company LIKE '%{currentCompany}%'"
                    cursor = db_conn.cursor()

                    try:
                        cursor.execute(select_sql)
                        jobApplication = cursor.fetchall()  # Fetch all students
                        company_application_list = []
                        for application in jobApplication:
                            applicationId = application[0]
                            applicationDateTime = application[1]
                            applicationStatus = application[2]

                            select_sql = f"SELECT s.studentId, s.studentName, s.mobileNumber, s.gender, s.address, s.email, s.level, s.programme, s.cohort FROM student s JOIN companyApplication ca ON s.studentId = ca.student WHERE ca.applicationId LIKE '%{currentCompany}%'"
                            cursor = db_conn.cursor()
                            cursor.execute(select_sql)
                            studentInfo = cursor.fetchall()
                            
                            for student in studentInfo:
                                stud_id = student[0]
                                stud_name = student[1]
                                stud_phone = student[2]
                                stud_gender = student[3]
                                stud_address = student[4]
                                stud_email = student[5]
                                stud_level = student[6]
                                stud_programme = student[7]
                                stud_cohort = student[8]
                                # Construct the S3 object key
                                object_key = str(stud_id) + "_resume"
                                # Generate a presigned URL for the S3 object
                                s3_client = boto3.client('s3')
                                try:
                                    response = s3_client.generate_presigned_url(
                                        'get_object',
                                        Params={
                                            'Bucket': custombucket,
                                            'Key': object_key,
                                            'ResponseContentDisposition': 'inline',
                                        },
                                        ExpiresIn=3600  # Set the expiration time (in seconds) as needed
                                    )
                                except ClientError as e:
                                    return str(e)
                                    # if e.response['Error']['Code'] == 'NoSuchKey':
                                    #     # If the resume does not exist, return a page with a message
                                    #     return render_template('home.html')
                                    # else:
                                    #     return str(e)
                                
                                application_data = {
                                        "application_id" : applicationId,
                                        "application_datetime" : applicationDateTime,
                                        "application_status" : applicationStatus,
                                        "student_id": stud_id,
                                        "stud_name": stud_name,
                                        "stud_phone": stud_phone,
                                        "stud_gender": stud_gender,
                                        "stud_address": stud_address,
                                        "stud_email": stud_email,
                                        "stud_level": stud_level,
                                        "stud_programme": stud_programme,
                                        "stud_cohort": stud_cohort,
                                        "stud_resume": response,
                                    }

                                # Append the student's dictionary to the student_list
                                # print(application_data)
                                company_application_list.append(application_data)
                            print("HAHA")    
                        # if action == 'drop':
                        #  return render_template('DropStudent.html', application_list=company_application_list,id=id)

                        # if action =='pickUp': 
                        #  return render_template('PickUpStudent.html', application_list=company_application_list)
                        return render_template('ViewCompanyApplication.html',id = session['logedInCompany'], name=company[2], applicationData = company_application_list)
                    except Exception as e:
                        return str(e)















                    # return render_template('ViewCompanyApplication.html', id = session['logedInCompany'], name = company[2])
                else:
                    return render_template('LoginCompany.html', msg="Registration still in progress")
            else:
                return render_template('LoginCompany.html', msg="Access Denied : Invalid email or password")
        except Exception as e:
            return str(e)
        
        finally:   
            cursor.close()
        
    return render_template('LoginCompany.html', msg="")

@app.route("/loginAdmin", methods=['GET','POST'])
def loginAdmin():
    if request.method == 'POST':
        admin_id = request.form['admin_ID']
        password = request.form['password']

        if admin_id != "Admin001" or password != "12345678":
            return render_template('LoginAdmin.html')
        session['logedInAdmin'] = str(admin_id)
        return render_template('AdminDashboard.html', id=session['logedInAdmin'])














































@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.tarc.edu.my')

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

